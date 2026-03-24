"""Send simple SMTP emails with attachments (stdlib only)."""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_email_with_image(
    *,
    to_addr: str,
    subject: str,
    body: str,
    image_path: Path,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    smtp_user: str | None = None,
    smtp_password: str | None = None,
    from_addr: str | None = None,
) -> None:
    smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = smtp_port if smtp_port is not None else int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = smtp_user or os.environ["SMTP_USER"]
    smtp_password = smtp_password or os.environ["SMTP_PASSWORD"]
    from_addr = from_addr or os.environ.get("EMAIL_FROM", smtp_user)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    data = image_path.read_bytes()
    msg.add_attachment(
        data,
        maintype="image",
        subtype="png",
        filename=image_path.name,
    )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)
