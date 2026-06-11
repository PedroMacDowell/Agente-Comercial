from __future__ import annotations

from email.message import EmailMessage
import smtplib
from pathlib import Path
from datetime import datetime

from .config import AppConfig
from .proposal import ProposalResult


def _write_email_draft(config: AppConfig, recipient_email: str, proposal: ProposalResult) -> Path:
    draft_dir = config.output_dir / "emails"
    draft_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = draft_dir / f"email-{timestamp}.eml"

    message = EmailMessage()
    message["To"] = recipient_email
    message["From"] = config.smtp_from or config.smtp_user or ""
    message["Subject"] = proposal.subject
    message.set_content(proposal.body)

    path.write_text(message.as_string(), encoding="utf-8")
    return path


def send_email(config: AppConfig, recipient_email: str, proposal: ProposalResult, send_now: bool = False) -> Path:
    draft_path = _write_email_draft(config, recipient_email, proposal)

    if not send_now:
        return draft_path

    if not config.smtp_host:
        raise RuntimeError("SMTP_HOST nao configurado.")
    if not config.smtp_user or not config.smtp_password:
        raise RuntimeError("SMTP_USER e SMTP_PASSWORD sao obrigatorios para envio.")

    message = EmailMessage()
    message["To"] = recipient_email
    message["From"] = config.smtp_from or config.smtp_user
    message["Subject"] = proposal.subject
    message.set_content(proposal.body)

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        if config.smtp_use_tls:
            smtp.starttls()
        smtp.login(config.smtp_user, config.smtp_password)
        smtp.send_message(message)

    return draft_path

