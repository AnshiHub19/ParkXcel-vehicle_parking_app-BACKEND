# mail.py
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "localhost"  # MailHog
SMTP_PORT = 1025         # MailHog port
FROM_EMAIL = "admin@example.com"

def send_mail(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
            print(f"Email sent to {to_email}")

    except Exception as e:
        print("Mail error:", e)
