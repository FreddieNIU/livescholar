"""功能：把 Markdown 文献报告转换为邮件正文，并通过 SMTP 发送给目标邮箱。"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from html import escape


def send_report_email(subject: str, markdown_body: str, report_path: str) -> None:
    required = {
        "LIVE_SCHOLAR_EMAIL_TO": os.getenv("LIVE_SCHOLAR_EMAIL_TO"),
        "LIVE_SCHOLAR_EMAIL_FROM": os.getenv("LIVE_SCHOLAR_EMAIL_FROM"),
        "LIVE_SCHOLAR_SMTP_HOST": os.getenv("LIVE_SCHOLAR_SMTP_HOST"),
        "LIVE_SCHOLAR_SMTP_PORT": os.getenv("LIVE_SCHOLAR_SMTP_PORT", "587"),
        "LIVE_SCHOLAR_SMTP_USERNAME": os.getenv("LIVE_SCHOLAR_SMTP_USERNAME"),
        "LIVE_SCHOLAR_SMTP_PASSWORD": os.getenv("LIVE_SCHOLAR_SMTP_PASSWORD"),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing email configuration: {', '.join(missing)}")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = required["LIVE_SCHOLAR_EMAIL_FROM"]
    message["To"] = required["LIVE_SCHOLAR_EMAIL_TO"]
    message.set_content(markdown_body)
    message.add_alternative(_markdownish_to_html(markdown_body), subtype="html")

    with open(report_path, "rb") as handle:
        message.add_attachment(
            handle.read(),
            maintype="text",
            subtype="markdown",
            filename=report_path.split("/")[-1],
        )

    with smtplib.SMTP(required["LIVE_SCHOLAR_SMTP_HOST"], int(required["LIVE_SCHOLAR_SMTP_PORT"])) as smtp:
        smtp.starttls()
        smtp.login(required["LIVE_SCHOLAR_SMTP_USERNAME"], required["LIVE_SCHOLAR_SMTP_PASSWORD"])
        smtp.send_message(message)


def _markdownish_to_html(markdown_body: str) -> str:
    lines = []
    for raw_line in markdown_body.splitlines():
        line = escape(raw_line)
        if line.startswith("# "):
            lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("- "):
            lines.append(f"<li>{line[2:]}</li>")
        elif line.strip():
            lines.append(f"<p>{line}</p>")
    return "<html><body>" + "\n".join(lines) + "</body></html>"
