"""Command line interface for translation quality utilities."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .checks import run_automated_checks
from .glossary import Glossary
from .sampling import sample_chapters
from .metrics import compute_bleu, MetricError


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def command_run_checks(args: argparse.Namespace) -> None:
    entries = load_jsonl(Path(args.input))
    report = run_automated_checks(entries)
    if args.output:
        Path(args.output).write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))


def command_glossary(args: argparse.Namespace) -> None:
    entries = load_jsonl(Path(args.input))
    glossary = Glossary.from_csv(args.glossary)
    issues = glossary.check_translation(entries)
    payload = [issue.__dict__ for issue in issues]
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def command_sample(args: argparse.Namespace) -> None:
    entries = load_jsonl(Path(args.input))
    samples = sample_chapters(entries, sample_size=args.sample_size, seed=args.seed)
    payload = [sample.__dict__ for sample in samples]
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def command_metrics(args: argparse.Namespace) -> None:
    translations = [item["translation"] for item in load_jsonl(Path(args.translations))]
    references = [item["reference"] for item in load_jsonl(Path(args.references))]
    try:
        bleu = compute_bleu(translations, references)
    except MetricError as exc:
        raise SystemExit(str(exc)) from exc
    payload = {"bleu": bleu}
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translation quality toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    checks_parser = subparsers.add_parser("run-checks", help="Run automated quality checks")
    checks_parser.add_argument("--input", required=True, help="JSONL file with translation entries")
    checks_parser.add_argument("--output", help="Path to write the report JSON")
    checks_parser.set_defaults(func=command_run_checks)

    glossary_parser = subparsers.add_parser("glossary", help="Check translations against a glossary")
    glossary_parser.add_argument("--input", required=True, help="JSONL file with translation entries")
    glossary_parser.add_argument("--glossary", required=True, help="CSV glossary file")
    glossary_parser.add_argument("--output", help="Path to write glossary inconsistencies")
    glossary_parser.set_defaults(func=command_glossary)

    sample_parser = subparsers.add_parser("sample", help="Sample paragraphs for manual review")
    sample_parser.add_argument("--input", required=True, help="JSONL file with translation entries")
    sample_parser.add_argument("--sample-size", type=int, default=5, help="Number of paragraphs to sample")
    sample_parser.add_argument("--seed", type=int, help="Random seed for reproducible sampling")
    sample_parser.add_argument("--output", help="Path to write the sampled paragraphs")
    sample_parser.set_defaults(func=command_sample)

    metrics_parser = subparsers.add_parser("metrics", help="Compute BLEU scores using references")
    metrics_parser.add_argument("--translations", required=True, help="JSONL file with system translations")
    metrics_parser.add_argument("--references", required=True, help="JSONL file with reference translations")
    metrics_parser.add_argument("--output", help="Where to write the metrics JSON")
    metrics_parser.set_defaults(func=command_metrics)

    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(args=argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
