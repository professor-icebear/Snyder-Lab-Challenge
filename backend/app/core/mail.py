from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Optional
import os

conf: Optional[ConnectionConfig] = None

# Only configure mail if all settings are present
if all(os.getenv(key) for key in ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_SERVER", "MAIL_FROM"]):
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
        USE_CREDENTIALS=os.getenv("USE_CREDENTIALS", "True").lower() == "true",
        VALIDATE_CERTS=os.getenv("VALIDATE_CERTS", "True").lower() == "true"
    )

fm: Optional[FastMail] = FastMail(conf) if conf else None

async def send_email(subject: str, recipients: List[EmailStr], body: str):
    if not fm:
        raise ConnectionError("Mail service is not configured. Please set MAIL_* environment variables.")
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype="html"
    )
    await fm.send_message(message) 