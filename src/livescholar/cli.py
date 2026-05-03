"""功能：提供 livescholar 命令行入口，连接配置、定时/手动运行、报告生成和邮件发送。"""

from __future__ import annotations

import argparse

from config.settings import load_settings
from utils.emailer import send_report_email
from utils.env import load_dotenv
from utils.run_logs import write_run_log
from utils.time_window import daily_window, is_scheduled_local_hour, rolling_24h_window

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LiveScholar daily literature monitor.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Search literature, generate a report, and email it.")
    add_run_arguments(run)
    run.add_argument(
        "--respect-schedule",
        action="store_true",
        help="Exit unless the current Europe/Dublin local hour is 07:00.",
    )

    manual = subparsers.add_parser(
        "manual",
        help="Search the rolling 24-hour window ending now, then generate the same report/email.",
    )
    add_run_arguments(manual)
    return parser


def add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="yaml/livescholar.yaml")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--log-dir", default="logs")
    parser.add_argument("--dry-run", action="store_true", help="Generate the report without sending email.")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {"run", "manual"}:
        settings = load_settings(args.config)
        if (
            args.command == "run"
            and args.respect_schedule
            and not is_scheduled_local_hour(timezone=settings.timezone)
        ):
            print(f"Skipping: current local hour is not 07:00 in {settings.timezone}.")
            return 0

        window = (
            daily_window(timezone=settings.timezone)
            if args.command == "run"
            else rolling_24h_window(timezone=settings.timezone)
        )
        report_path, body, papers, search_log = run_pipeline(settings, window, args.output_dir)
        log_path = write_run_log(search_log, papers, window, args.log_dir)
        subject = f"LiveScholar: {len(papers)} semantic-ID recommender papers ({window.end:%Y-%m-%d})"
        if args.dry_run:
            print(f"Dry run complete. Report written to {report_path}; log written to {log_path}")
            return 0
        send_report_email(subject, body, str(report_path))
        print(f"Email sent. Report written to {report_path}; log written to {log_path}")
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
