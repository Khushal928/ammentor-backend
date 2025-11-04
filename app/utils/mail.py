import smtplib
from email.message import EmailMessage
import os


from dotenv import load_dotenv
load_dotenv()

EMAIL_ADDRESS = os.getenv("SMTP_EMAIL")
EMAIL_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your OTP Verification Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(f"Your OTP is: {otp}\n\nThis OTP is valid for 5 minutes.")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"OTP sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")