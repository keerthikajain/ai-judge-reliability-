"""CLI entry point for Stage 2.

Usage
-----
Dry run (no key, no network):
    python -m src.stage2.run_stage2 --dry-run

One live request:
    python -m src.stage2.run_stage2 --limit 1

Resume remaining requests:
    python -m src.stage2.run_stage2 --resume
"""
import argparse
import sys

from src.stage2.runner import run


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage 2 Gemini judge runner for the AI-judge-reliability pilot."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and validate the manifest; make zero network calls. No API key needed.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N requests (e.g. 1 for a single live test).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Skip already-completed requests. "
            "Refuses to continue if dataset, prompts, model or settings have changed."
        ),
    )
    args = parser.parse_args()

    if args.dry_run and args.limit is not None:
        parser.error("--dry-run and --limit cannot be combined.")

    try:
        run(dry_run=args.dry_run, limit=args.limit, resume=args.resume)
    except EnvironmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
