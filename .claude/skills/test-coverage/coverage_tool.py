#!/usr/bin/env python3
"""Deterministic coverage helper for the test-coverage skill. Stdlib only, works in any Python project.

Commands (all print plain text, exit code 0 unless stated):
  run      Run pytest with coverage and write a coverage.json (extra pytest args after `--`).
  summary  Total % plus per-package table, worst first.
  files    Files ranked by missed lines (biggest payoff first).
  funcs    Functions never executed (function coverage), ranked by size.
  lines    Missing line ranges of one file (use after funcs, for branch/line work).
  gate     Exit 1 if total coverage is below --min.
  compare  Show total/file deltas between two coverage.json files (feedback loop after a test batch).

Example:
  python coverage_tool.py run --source src/backend -- -m "not slow" -n 4
  python coverage_tool.py funcs --top 20
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_JSON = Path("tmp/analysis/coverage.json")


def load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"{path} not found. Run: python {Path(__file__).name} run")
    return json.loads(path.read_text(encoding="utf-8"))


def pct(covered: int, total: int) -> float:
    return 100.0 * covered / total if total else 100.0


def package_of(filename: str, depth: int) -> str:
    parts = Path(filename).parts
    # Drop the file name; keep the first `depth` directories after the source root marker if present.
    dirs = parts[:-1]
    if "backend" in dirs:
        dirs = dirs[dirs.index("backend") + 1 :]
    return ".".join(dirs[:depth]) or "(root)"


def cmd_run(args: argparse.Namespace, pytest_args: list[str]) -> int:
    args.json.parent.mkdir(parents=True, exist_ok=True)
    runner = ["uv", "run", "pytest"] if shutil.which("uv") else [sys.executable, "-m", "pytest"]
    cmd = [*runner, f"--cov={args.source}", f"--cov-report=json:{args.json}", "--cov-report=term", *pytest_args]
    print("+", " ".join(cmd), flush=True)
    code = subprocess.call(cmd)
    if args.json.exists():
        d = load(args.json)["totals"]
        print(f"\nTOTAL {d['percent_covered']:.1f}% ({d['covered_lines']}/{d['num_statements']} lines) -> {args.json}")
    return code


def cmd_summary(args: argparse.Namespace) -> int:
    data = load(args.json)
    t = data["totals"]
    print(f"TOTAL {t['percent_covered']:.1f}%  statements={t['num_statements']}  missing={t['missing_lines']}")
    pk: dict[str, list[int]] = {}
    for name, f in data["files"].items():
        s = f["summary"]
        row = pk.setdefault(package_of(name, args.depth), [0, 0])
        row[0] += s["covered_lines"]
        row[1] += s["num_statements"]
    print(f"\n{'package':45} {'cover':>7} {'stmts':>6} {'missed':>6}")
    for name, (cov, tot) in sorted(pk.items(), key=lambda kv: kv[1][1] - kv[1][0], reverse=True):
        print(f"{name:45} {pct(cov, tot):6.1f}% {tot:6d} {tot - cov:6d}")
    return 0


def cmd_files(args: argparse.Namespace) -> int:
    rows = [(n, f["summary"]) for n, f in load(args.json)["files"].items() if f["summary"]["num_statements"]]
    rows.sort(key=lambda r: r[1]["missing_lines"], reverse=True)
    print(f"{'missed':>6} {'cover':>7} {'stmts':>6}  file")
    for name, s in rows[: args.top]:
        print(f"{s['missing_lines']:6d} {s['percent_covered']:6.1f}% {s['num_statements']:6d}  {name}")
    return 0


def uncovered_functions(filename: str, executed: set[int], missing: set[int]) -> list[tuple[str, int, int, int]]:
    """Return (qualified name, first line, last line, missed statements) for functions never executed."""
    path = Path(filename)
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[tuple[str, int, int, int]] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_lines = set(range(child.body[0].lineno, (child.end_lineno or child.lineno) + 1))
                if not (body_lines & executed) and (body_lines & missing):
                    out.append((prefix + child.name, child.lineno, child.end_lineno or child.lineno, len(body_lines & missing)))
                visit(child, prefix + child.name + ".")
            elif isinstance(child, ast.ClassDef):
                visit(child, prefix + child.name + ".")

    visit(tree, "")
    return out


def cmd_funcs(args: argparse.Namespace) -> int:
    rows = []
    total_funcs = 0
    for name, f in load(args.json)["files"].items():
        executed, missing = set(f["executed_lines"]), set(f["missing_lines"])
        rows += [(name, *r) for r in uncovered_functions(name, executed, missing)]
        total_funcs += 1
    rows.sort(key=lambda r: r[4], reverse=True)
    print(f"{len(rows)} functions never executed (showing {min(args.top, len(rows))}); missed = statements\n")
    print(f"{'missed':>6}  location")
    for file, qual, first, _last, missed in rows[: args.top]:
        print(f"{missed:6d}  {file}:{first}  {qual}")
    return 0


def compress(nums: list[int]) -> str:
    ranges, start, prev = [], None, None
    for n in sorted(nums):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            ranges.append((start, prev))
            start = prev = n
    if start is not None:
        ranges.append((start, prev))
    return ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in ranges)


def cmd_lines(args: argparse.Namespace) -> int:
    files = load(args.json)["files"]
    matches = [n for n in files if n.replace("\\", "/").endswith(args.file.replace("\\", "/"))]
    if len(matches) != 1:
        sys.exit(f"Expected one match for {args.file!r}, got {matches}")
    f = files[matches[0]]
    print(f"{matches[0]}: {f['summary']['percent_covered']:.1f}%")
    print("missing lines:", compress(f["missing_lines"]) or "none")
    if f.get("missing_branches"):
        print("missing branches (from->to):", ", ".join(f"{a}->{b}" for a, b in f["missing_branches"][:40]))
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    total = load(args.json)["totals"]["percent_covered"]
    ok = total >= args.min
    print(f"coverage {total:.1f}% {'>=' if ok else '<'} gate {args.min}%")
    return 0 if ok else 1


def cmd_compare(args: argparse.Namespace) -> int:
    old, new = load(args.old), load(args.json)
    print(f"TOTAL {old['totals']['percent_covered']:.1f}% -> {new['totals']['percent_covered']:.1f}%\n")
    deltas = []
    for name, f in new["files"].items():
        before = old["files"].get(name, {"summary": {"percent_covered": 0.0, "missing_lines": 0}})["summary"]
        d = f["summary"]["percent_covered"] - before["percent_covered"]
        if abs(d) >= 0.05:
            deltas.append((d, name, before["percent_covered"], f["summary"]["percent_covered"]))
    for d, name, b, a in sorted(deltas, reverse=True):
        print(f"{d:+6.1f}  {b:5.1f}% -> {a:5.1f}%  {name}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    pytest_args: list[str] = []
    if "--" in argv:
        i = argv.index("--")
        argv, pytest_args = argv[:i], argv[i + 1 :]
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", type=Path, default=DEFAULT_JSON, help="coverage.json path (default: %(default)s)")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--source", default="src", help="package/dir to measure (default: %(default)s)")
    s = sub.add_parser("summary")
    s.add_argument("--depth", type=int, default=1, help="package depth below the source root")
    for name in ("files", "funcs"):
        sp = sub.add_parser(name)
        sp.add_argument("--top", type=int, default=15)
    sub.add_parser("lines").add_argument("file", help="file path or suffix")
    sub.add_parser("gate").add_argument("--min", type=float, required=True)
    sub.add_parser("compare").add_argument("old", type=Path, help="earlier coverage.json")
    args = p.parse_args(argv)
    handlers = {
        "summary": cmd_summary, "files": cmd_files, "funcs": cmd_funcs,
        "lines": cmd_lines, "gate": cmd_gate, "compare": cmd_compare,
    }  # fmt: skip
    return cmd_run(args, pytest_args) if args.cmd == "run" else handlers[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
