from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import load_settings
from .emailer import send_report_email
from .pipeline import run_pipeline
from .time_window import daily_window, is_scheduled_local_hour


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LiveScholar daily literature monitor.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Search literature, generate a report, and email it.")
    run.add_argument("--config", default="config.yaml")
    run.add_argument("--output-dir", default="reports")
    run.add_argument("--dry-run", action="store_true", help="Generate the report without sending email.")
    run.add_argument(
        "--respect-schedule",
        action="store_true",
        help="Exit unless the current Europe/Dublin local hour is 07:00.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        settings = load_settings(args.config)
        if args.respect_schedule and not is_scheduled_local_hour(timezone=settings.timezone):
            print(f"Skipping: current local hour is not 07:00 in {settings.timezone}.")
            return 0

        window = daily_window(timezone=settings.timezone)
        report_path, body, papers, _search_log = run_pipeline(settings, window, args.output_dir)
        subject = f"LiveScholar: {len(papers)} semantic-ID recommender papers ({window.end:%Y-%m-%d})"
        if args.dry_run:
            print(f"Dry run complete. Report written to {report_path}")
            return 0
        send_report_email(subject, body, str(report_path))
        print(f"Email sent. Report written to {report_path}")
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

