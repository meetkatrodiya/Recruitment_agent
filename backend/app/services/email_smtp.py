import os
import smtplib
from email.mime.text import MIMEText
from fastapi import HTTPException


def send_email_smtp(to_email: str, subject: str, body_text: str, from_name: str | None = None) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", username or "")

    if not host or not username or not password or not from_email:
        raise HTTPException(status_code=500, detail="SMTP configuration is incomplete")

    msg = MIMEText(body_text)
    msg["Subject"] = subject
    msg["From"] = f"{from_name or 'HR Team'} <{from_email}>"
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_email, [to_email], msg.as_string())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"SMTP send failed: {exc}") 