"""CLI entry point for the main-study Stage 2 runner.

Reuses the existing runner's timeout, bounded retries, immediate saving,
resume protection and configuration-change checks.

Usage
-----
Dry run (no key, no network):
    python -m src.stage2.run_main_stage2 --dry-run

One live request:
    python -m src.stage2.run_main_stage2 --limit 1

Resume remaining requests:
    python -m src.stage2.run_main_stage2 --resume
"""
import argparse
import sys

# Patch the runner module to use main-study paths and manifest builder
# BEFORE importing run() from it.
import src.stage2.runner as _runner
from pathlib import Path

_MAIN_ROOT = Path(__file__).resolve().parents[2]
_MAIN_OUTPUTS = _MAIN_ROOT / "outputs" / "main" / "stage2"

_runner.MANIFEST_PATH = _MAIN_OUTPUTS / "manifest.json"
_runner.RESULTS_PATH = _MAIN_OUTPUTS / "results.jsonl"
_runner.DRY_RUN_RESULTS_PATH = _MAIN_OUTPUTS / "dry_run" / "results.jsonl"

# Patch the manifest functions imported by runner
from src.stage2.main_experiment import (
    build_main_manifest as _build,
    config_fingerprint as _fingerprint,
    save_manifest as _save,
    load_manifest as _load,
)

_runner.build_manifest = _build
_runner.config_fingerprint = _fingerprint
_runner.save_manifest = _save
_runner.load_manifest = _load


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Main-study Stage 2 Gemini judge runner (120 requests)."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Build and validate the manifest; zero network calls.")
    parser.add_argument("--limit", type=int, default=None, metavar="N",
                        help="Stop after N requests.")
    parser.add_argument("--resume", action="store_true",
                        help="Skip completed requests; refuse if config changed.")
    args = parser.parse_args()

    if args.dry_run and args.limit is not None:
        parser.error("--dry-run and --limit cannot be combined.")

    try:
        _runner.run(dry_run=args.dry_run, limit=args.limit, resume=args.resume)
    except EnvironmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
