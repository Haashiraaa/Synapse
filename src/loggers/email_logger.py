

# src/loggers/email_logger.py


import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from src.loggers.base import BaseAlertLogger
from src.config.settings import Settings
from src.exceptions.errors import EmailAuthError, EmailDeliveryError
from haashi_pkg.utility import Logger


class EmailAlertLogger(BaseAlertLogger):
    """
    Sends alert emails via Gmail SMTP (or any SMTP provider).

    Required .env vars:
        ALERT_EMAIL_FROM      — sender Gmail address
        ALERT_EMAIL_TO        — recipient email address
        ALERT_EMAIL_PASSWORD  — Gmail App Password (not your account password)
                                Generate at: myaccount.google.com/apppasswords

    Gmail setup:
        1. Enable 2FA on your Google account
        2. Go to myaccount.google.com/apppasswords
        3. Generate an app password for "Mail"
        4. Use that 16-char password as ALERT_EMAIL_PASSWORD
    """

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587

    def __init__(
        self,
        logger: Optional[Logger] = None
    ) -> None:

        self.logger = logger or Logger(level=logging.INFO)

        self.from_addr: str = Settings.ALERT_EMAIL_FROM or ""
        self.to_addr: str = Settings.ALERT_EMAIL_TO or ""
        self.password: str = Settings.ALERT_EMAIL_PASSWORD or ""

        self.configured = all([self.from_addr, self.to_addr, self.password])

    def send(self, subject: str, body: str) -> None:

        if not self.configured:
            self.logger.warning("Email alerts are not configured. Skipping...")
            return

        msg = MIMEMultipart()
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(self.from_addr, self.password)
                server.sendmail(self.from_addr, self.to_addr, msg.as_string())

            self.logger.info(f"Email alert sent: {subject}")

        except smtplib.SMTPAuthenticationError as exc:
            self.logger.error(
                "Email auth failed — check ALERT_EMAIL_PASSWORD. "
                "Make sure you're using a Gmail App Password, not your account password."
            )
            raise EmailAuthError(
                "SMTP authentication failed. Use a Gmail App Password, not your account password."
            ) from exc

        except Exception as exc:
            self.logger.error(f"Failed to send email alert: {exc}")
            raise EmailDeliveryError(
                f"Failed to deliver email alert: {exc}"
            ) from exc
