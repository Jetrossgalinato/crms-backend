from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your_email@gmail.com"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your_app_password"),
            MAIL_FROM=os.getenv("MAIL_FROM", "your_email@gmail.com"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        self.fast_mail = FastMail(self.conf)

    async def send_warning_email(self, email: List[EmailStr], subject: str, body: str):
        message = MessageSchema(
            subject=subject,
            recipients=email,
            body=body,
            subtype=MessageType.html
        )
        await self.fast_mail.send_message(message)

email_service = EmailService()
