<!-- 功能：说明 LiveScholar 项目结构、配置方式、运行命令、手动执行和 GitHub Actions 每周定时任务。 -->

# livescholar

LiveScholar is a weekly literature monitor for generative and multimodal recommender-system papers, including work related to semantic IDs, generative retrieval, LLM-based recommendation, item tokenization, and multimodal item representations. It searches recent arXiv and Google Scholar candidates, filters for recommendation relevance, highlights industry-affiliated work, generates a Markdown/HTML report, writes an execution log, and emails the report to the configured recipient.

## What It Does

- Runs automatically every Monday in `Europe/Dublin`.
- Searches a 240-hour scheduled window ending at the current scheduled execution time.
- Supports manual execution with a rolling 24-hour search window ending at the current time.
- Searches arXiv directly.
- Optionally searches Google Scholar through SerpAPI.
- Enriches paper metadata through OpenAlex and Semantic Scholar.
- Scores papers by semantic-ID/generative-retrieval terminology, recommendation-system relevance, and industry affiliation.
- Generates the same report format for scheduled and manual runs.
- Sends the report by SMTP and stores local run records.

## Project Structure

```text
.
├── main.py                  # Main local entrypoint
├── src/livescholar/         # Search sources, filtering, pipeline, report rendering, CLI
├── utils/                   # Environment loading, email, time windows, run logs
├── config/                  # Typed settings model and YAML loader
├── yaml/                    # Editable runtime YAML configuration
├── reports/                 # Generated Markdown reports, ignored by Git
├── logs/                    # Generated execution logs, ignored by Git
├── tests/                   # Unit tests
└── .github/workflows/       # GitHub Actions scheduler and manual dispatch
```

Every tracked file starts with a short function comment describing its role.

## Install Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` with your email and optional search API credentials.

## Configuration

Main search settings live in [yaml/livescholar.yaml](/Users/freddie/Documents/livescholar/yaml/livescholar.yaml):

- `timezone`: defaults to `Europe/Dublin`.
- `topic`: report scope.
- `max_results_per_source`: per-query retrieval limit.
- `min_relevance_score`: screening threshold.
- `queries`: broad search terms for generative, multimodal, LLM-based, and semantic-ID recommendation work.
- `industry_affiliations`: company names used to highlight industrial papers.

## Environment Variables

Required for sending email:

- `LIVE_SCHOLAR_EMAIL_TO`: recipient email address.
- `LIVE_SCHOLAR_EMAIL_FROM`: sender email address.
- `LIVE_SCHOLAR_SMTP_HOST`: SMTP server hostname.
- `LIVE_SCHOLAR_SMTP_PORT`: SMTP port, usually `587`.
- `LIVE_SCHOLAR_SMTP_USERNAME`: SMTP username.
- `LIVE_SCHOLAR_SMTP_PASSWORD`: SMTP password or app password.

Optional:

- `SERPAPI_API_KEY`: enables Google Scholar discovery.
- `SEMANTIC_SCHOLAR_API_KEY`: increases Semantic Scholar API limits.

## Run Modes

Scheduled semantics:

```bash
python main.py run --dry-run
```

By default this searches from yesterday 07:00 Ireland time to now. In GitHub Actions, scheduled runs add `--respect-schedule --window-hours 240`, so the weekly job exits unless the local Ireland day is Monday and then searches the previous 240 hours.

Manual semantics:

```bash
python main.py manual --dry-run
```

This detects the current time automatically and searches the previous 24 hours. The output report format is the same as the scheduled run.

For debugging search coverage, override either mode with a longer rolling window ending now:

```bash
python main.py manual --dry-run --window-hours 240
```

This example matches the scheduled 240-hour weekly window. Use `720` for roughly 30 days.

Installed CLI equivalents:

```bash
livescholar run --dry-run
livescholar manual --dry-run
```

Remove `--dry-run` to send email.

## Outputs

- Reports are written to `reports/livescholar-YYYY-MM-DD.md`.
- Logs are written to `logs/run-YYYYMMDD-HHMMSS.log`.
- Generated report and log files are ignored by Git.
- `reports/README.md` and `logs/README.md` are tracked to keep the folder purposes visible.

## GitHub Actions

The workflow is in [.github/workflows/daily-literature.yml](/Users/freddie/Documents/livescholar/.github/workflows/daily-literature.yml).

GitHub cron uses UTC and does not support time zones, and scheduled jobs may start late. The workflow wakes once every Monday at `07:00` UTC. The command then checks whether the current local day in `Europe/Dublin` is Monday before doing work. Scheduled runs use `--window-hours 240`.

Manual `workflow_dispatch` runs use:

```bash
livescholar manual
```

That gives an on-demand rolling 24-hour report.

Add these GitHub repository secrets before enabling email delivery:

```text
LIVE_SCHOLAR_EMAIL_TO
LIVE_SCHOLAR_EMAIL_FROM
LIVE_SCHOLAR_SMTP_HOST
LIVE_SCHOLAR_SMTP_PORT
LIVE_SCHOLAR_SMTP_USERNAME
LIVE_SCHOLAR_SMTP_PASSWORD
SERPAPI_API_KEY
SEMANTIC_SCHOLAR_API_KEY
```

Only the SMTP variables are mandatory.

## Local Cron

For a local machine configured with timezone support:

```cron
0 7 * * 1 cd /path/to/livescholar && . .venv/bin/activate && livescholar run --window-hours 240
```

## Validation

```bash
python -m pytest
python -m ruff check .
python main.py run --dry-run --window-hours 240
```

## Notes On Search Coverage

Google Scholar does not provide an official public API. This project uses SerpAPI when `SERPAPI_API_KEY` is present and records a clear search-log note when it is missing. arXiv search still runs without Google Scholar credentials.
