"""CLI for RAG evaluation.

Run: uv run evaluate-rag --dataset path/to/benchmark.json [--output out] [--configs dense hybrid]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _format_markdown(report: dict) -> str:
    """Format evaluation report as markdown table."""
    lines = [
        "## RAG Evaluation Report",
        "",
        "| Strategy | MRR | Recall@5 | Hit@5 | Precision@5 |",
        "|----------|-----|----------|-------|-------------|",
    ]
    for config_name, data in report.items():
        agg = data.get("aggregates", {})
        mrr_val = agg.get("mrr", 0)
        rec = agg.get("recall_at_5", 0)
        hit = agg.get("hit_at_5", 0)
        prec = agg.get("precision_at_5", 0)
        lines.append(f"| {config_name} | {mrr_val:.4f} | {rec:.4f} | {hit:.4f} | {prec:.4f} |")
    return "\n".join(lines)


def main() -> int:
    """Run evaluation CLI."""
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval on a benchmark dataset")
    parser.add_argument(
        "--dataset",
        "-d",
        required=True,
        help="Path to benchmark JSON file (question, ground_truth_contexts)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output base path (creates .json and .md). Default: print JSON to stdout",
    )
    parser.add_argument(
        "--configs",
        "-c",
        nargs="+",
        default=None,
        help="Configs to compare (default: dense sparse hybrid)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Retrieval top-k (default: 5)",
    )
    args = parser.parse_args()

    from backend.rag_pipeline.evaluation.runner import run_evaluation

    try:
        report = run_evaluation(
            dataset_path=args.dataset,
            configs=args.configs,
            top_k=args.top_k,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise

    json_str = json.dumps(report, indent=2)
    if args.output:
        out_base = Path(args.output)
        out_base.parent.mkdir(parents=True, exist_ok=True)
        json_path = out_base.with_suffix(".json") if out_base.suffix != ".json" else out_base
        md_path = json_path.with_suffix(".md")
        json_path.write_text(json_str, encoding="utf-8")
        md_path.write_text(_format_markdown(report), encoding="utf-8")
        print(f"Wrote {json_path} and {md_path}")
    else:
        print(json_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
