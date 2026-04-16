import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_otp_email(to_email: str, otp: str):
    try:
        # email content
        subject = "Password Reset - ChefJunior App"
        body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hello,</p>
                <p>You requested to reset your password. Your OTP code is:</p>
                <h1 style="color: #FF5722;">{otp}</h1>
                <p>This code expires in 10 minutes.</p>
                <p>If you did not request this, please ignore this email.</p>
            </body>
        </html>
        """

        # Setup MIME
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail Server
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
            
        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_email_verification_otp(to_email: str, otp: str):
    """
    Send email verification OTP to user's email address.
    OTP expires in 2 minutes.
    """
    try:
        # Email content
        subject = "Verify Your Email - ChefJunior App"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #333;">Welcome to ChefJunior!</h2>
                    <p style="color: #666; font-size: 16px;">Hello,</p>
                    <p style="color: #666; font-size: 16px;">Thank you for signing up. Please verify your email address by entering the code below:</p>
                    
                    <div style="background-color: #FF5722; color: white; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="margin: 0; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                    </div>
                    
                    <p style="color: #999; font-size: 14px;"><strong>This code expires in 2 minutes.</strong></p>
                    <p style="color: #666; font-size: 16px;">If you did not create this account, please ignore this email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">© 2026 ChefJunior. All rights reserved.</p>
                </div>
            </body>
        </html>
        """

        # Setup MIME
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail Server
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
            
        print(f"Email verification OTP sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email verification: {e}")
        return False