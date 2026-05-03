<!-- 功能：说明 LiveScholar 项目结构、配置方式、运行命令和 GitHub Actions 定时任务。 -->

# livescholar

Daily literature monitor for recommender-system papers about semantic IDs.

The job runs once per day at 07:00 Europe/Dublin time, searches papers posted or updated since 07:00 the previous day, highlights industry-affiliated work, generates a Markdown/HTML report, and emails it to the configured recipient.

## Project Structure

```text
.
├── main.py                  # Main local entrypoint
├── src/livescholar/         # Literature search, filtering, pipeline, and report domain code
├── utils/                   # Environment, time window, email, and run-log helpers
├── config/                  # Typed settings model and YAML loader
├── yaml/                    # Editable runtime YAML configuration
├── reports/                 # Generated Markdown reports
├── logs/                    # Generated execution logs
├── tests/                   # Unit tests
└── .github/workflows/       # GitHub Actions scheduler
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python main.py run --dry-run
```

The installed CLI is equivalent:

```bash
livescholar run --dry-run
```

## Required Secrets

Set these in `.env` locally or as GitHub Actions secrets:

- `LIVE_SCHOLAR_EMAIL_TO`: recipient email address.
- `LIVE_SCHOLAR_EMAIL_FROM`: sender email address.
- `LIVE_SCHOLAR_SMTP_HOST`: SMTP server hostname.
- `LIVE_SCHOLAR_SMTP_PORT`: SMTP port, usually `587`.
- `LIVE_SCHOLAR_SMTP_USERNAME`: SMTP username.
- `LIVE_SCHOLAR_SMTP_PASSWORD`: SMTP password or app password.

Optional:

- `SERPAPI_API_KEY`: enables Google Scholar discovery through SerpAPI.
- `SEMANTIC_SCHOLAR_API_KEY`: raises Semantic Scholar API limits when verifying papers.

## GitHub Actions Schedule

GitHub cron uses UTC and does not support time zones. The workflow therefore wakes at both `06:00` and `07:00` UTC and the program exits unless the current local time in `Europe/Dublin` is exactly 07:00. This handles Irish winter/summer time without editing the schedule twice per year.

## Local Cron

For a machine configured with timezone support:

```cron
0 7 * * * cd /path/to/livescholar && . .venv/bin/activate && livescholar run
```

## Validation

```bash
python -m pytest
python -m ruff check .
```
