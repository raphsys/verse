# app/utils/email_sender.py

import smtplib
from email.message import EmailMessage

def send_email(to_email: str, subject: str, body: str):
    # Remplace ces variables par tes vrais identifiants
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "ton_adresse@gmail.com"
    SMTP_PASSWORD = "motdepasse_app"

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

