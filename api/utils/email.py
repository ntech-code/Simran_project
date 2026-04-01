import smtplib
from email.message import EmailMessage
import os
import random
import string
from dotenv import load_dotenv

load_dotenv()

# The provided credentials
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "aeindra2528@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "prar oerb fgla gwxi")

def generate_otp(length=6):
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email: str, otp: str, request_type: str = "signup"):
    """
    Sends an OTP to the given email address.
    request_type can be 'signup' or 'reset_password'
    """
    try:
        msg = EmailMessage()
        if request_type == "signup":
            msg.set_content(f"Welcome to the Indian Tax Analysis System!\n\nYour One-Time Password (OTP) for registration is:\n\n{otp}\n\nThis OTP is valid for 10 minutes.\n\nDo not share this OTP with anyone.")
            msg['Subject'] = 'Your OTP for Tax Analysis System Registration'
        elif request_type == "reset_password":
            msg.set_content(f"You requested a password reset for the Indian Tax Analysis System.\n\nYour One-Time Password (OTP) to reset your password is:\n\n{otp}\n\nThis OTP is valid for 10 minutes.\n\nIf you did not request this, please ignore this email.")
            msg['Subject'] = 'Password Reset OTP - Tax Analysis System'
        
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email

        # Send the message via our own SMTP server.
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
