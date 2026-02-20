#!/usr/bin/env python3
"""Identify slow tests by parsing pytest JUnit XML output.

As a developer I want to see which tests take the most time, so I can optimize
or prioritize them. This script runs pytest with --junit-xml, parses the
results, and outputs a sorted table of test durations with optional highlighting
for tests above a configurable threshold.

Technical: Uses xml.etree.ElementTree to parse JUnit XML. Supports unit test
threshold (default 1s) and integration threshold (default 5s) for highlighting.

Created: 2025-02-20
"""

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _classname_to_file(classname: str) -> str:
    """Convert pytest classname to test file path.

    Args:
        classname: e.g. 'tests.test_document_loader.TestDocumentLoader'

    Returns:
        e.g. 'tests/test_document_loader.py'
    """
    if not classname:
        return ""
    parts = classname.split(".")
    module_parts = [p for p in parts if p and not p[0].isupper()]
    return "/".join(module_parts) + ".py" if module_parts else classname.replace(".", "/") + ".py"


def parse_junit_xml(xml_path: Path) -> list[dict]:
    """Extract test names, durations, and file paths from JUnit XML.

    Args:
        xml_path: Path to JUnit XML file (e.g. from pytest --junit-xml).

    Returns:
        List of dicts with keys: name, duration, file, classname.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results: list[dict] = []
    for suite in root.iter("testsuite"):
        for case in suite.iter("testcase"):
            name = case.get("name", "unknown")
            classname = case.get("classname", "")
            time_attr = case.get("time")
            duration = float(time_attr) if time_attr else 0.0

            # Derive file path from classname (e.g. tests.test_document_loader.TestDocumentLoader -> tests/test_document_loader.py)
            file_path = _classname_to_file(classname)

            results.append(
                {
                    "name": name,
                    "duration": duration,
                    "file": file_path,
                    "classname": classname,
                }
            )
    return results


def format_table(rows: list[dict], unit_threshold: float, integration_threshold: float) -> str:
    """Format results as a markdown table with highlight markers.

    Args:
        rows: List of test result dicts (pre-sorted by duration descending).
        unit_threshold: Seconds above which unit tests are highlighted.
        integration_threshold: Seconds above which integration tests are highlighted.

    Returns:
        Markdown table string.
    """
    lines = []
    lines.append("| Duration (s) | Test | File |")
    lines.append("|-------------|------|------|")

    for r in rows:
        duration = r["duration"]
        marker = ""
        if "integration" in r["file"].lower() or "internet" in r["classname"].lower():
            if duration >= integration_threshold:
                marker = " [SLOW]"
        elif duration >= unit_threshold:
            marker = " [SLOW]"
        lines.append(f"| {duration:.2f}{marker} | {r['name']} | {r['file']} |")

    return "\n".join(lines)


def run_pytest_and_parse(
    junit_path: Path,
    marker: str = "not slow and not internet and not ollama and not docker and not guardrails_ci_skip and not ci_skip",
) -> int:
    """Run pytest with JUnit XML output and return exit code.

    Args:
        junit_path: Where to write JUnit XML.
        marker: Pytest marker expression for test selection.

    Returns:
        Pytest exit code (0 = pass).
    """
    cmd = [
        "uv",
        "run",
        "pytest",
        "-m",
        marker,
        f"--junitxml={junit_path}",
        "-q",
    ]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def main() -> int:
    """Parse args, run or parse JUnit XML, and print timing report."""
    parser = argparse.ArgumentParser(
        description="Identify slow tests from pytest JUnit XML output.",
    )
    parser.add_argument(
        "--xml",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "junit-timing.xml",
        help="Path to JUnit XML file (default: tmp/junit-timing.xml)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run pytest first to generate XML (otherwise parse existing file)",
    )
    parser.add_argument(
        "--unit-threshold",
        type=float,
        default=1.0,
        help="Highlight unit tests above this duration in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--integration-threshold",
        type=float,
        default=5.0,
        help="Highlight integration tests above this duration (default: 5.0)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Show only top N slowest tests (default: 20)",
    )
    args = parser.parse_args()

    xml_path = args.xml.resolve()
    if args.run:
        xml_path.parent.mkdir(parents=True, exist_ok=True)
        rc = run_pytest_and_parse(xml_path)
        if rc != 0:
            print(f"pytest exited with code {rc}", file=sys.stderr)
            return rc

    if not xml_path.exists():
        print(f"JUnit XML not found: {xml_path}", file=sys.stderr)
        print("Run with --run to generate it first.", file=sys.stderr)
        return 1

    rows = parse_junit_xml(xml_path)
    if not rows:
        print("No test results found in XML.", file=sys.stderr)
        return 1

    rows_sorted = sorted(rows, key=lambda x: -x["duration"])[: args.top]
    table = format_table(rows_sorted, args.unit_threshold, args.integration_threshold)
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
