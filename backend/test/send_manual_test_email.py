#!/usr/bin/env python
# Test script to manually send a test email to debug email delivery issues

import sys
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dotenv
import argparse

# Load environment variables from .env file
dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def send_test_email(recipient_email):
    """
    Send a test email to the recipient
    """
    # Email configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("EMAIL_SENDER", "")
    username = os.getenv("EMAIL_USERNAME", sender_email)
    sender_password = os.getenv("EMAIL_PASSWORD", "")
    use_tls = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    
    # Check if email configuration is set
    if not sender_email or not sender_password:
        print("Email configuration is missing. Please set EMAIL_SENDER and EMAIL_PASSWORD environment variables.")
        print(f"Current config: SMTP_SERVER={smtp_server}, SMTP_PORT={smtp_port}, EMAIL_SENDER={sender_email}")
        return False
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Test Email - Language Tutor License Key"
    message["From"] = sender_email
    message["To"] = recipient_email
    
    # Generate a fake license key for testing
    license_key = "ABCD-1234-EFGH-5678"
    
    # Add text content
    text_content = f"""Hello User,

This is a test email to verify email delivery for Language Tutor.
Your test license key is: {license_key}

If you received this email, it means the email delivery is working correctly.

Best regards,
The Language Tutor Team
"""
    text_part = MIMEText(text_content, "plain")
    message.attach(text_part)
    
    # Add HTML content
    html_content = f"""
<html>
<head></head>
<body>
    <p>Hello User,</p>
    
    <p>This is a test email to verify email delivery for Language Tutor.</p>
    <p>Your test license key is:</p>
    
    <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; font-family: monospace; font-size: 18px; text-align: center;">
        {license_key}
    </div>
    
    <p>If you received this email, it means the email delivery is working correctly.</p>
    
    <p>Best regards,<br>
    The Language Tutor Team</p>
</body>
</html>
"""
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)
    
    try:
        print(f"Sending test email to {recipient_email}...")
        print(f"Using SMTP server: {smtp_server}:{smtp_port}")
        print(f"Sender: {sender_email}")
        print(f"Username: {username}")
        
        # Create secure connection with the SMTP server
        context = ssl.create_default_context()
        
        # Connect to SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("Connected to SMTP server")
            
            # Secure the connection
            if use_tls:
                print("Starting TLS...")
                server.starttls(context=context)
            
            # Login to the SMTP server using username (which may be different from sender email)
            print(f"Logging in with username: {username}...")
            server.login(username, sender_password)
            
            # Send email
            print("Sending email...")
            server.sendmail(
                sender_email, 
                recipient_email, 
                message.as_string()
            )
        
        print(f"Email sent successfully to {recipient_email}")
        
        # If using Mailtrap, provide the correct view URL
        if "mailtrap" in smtp_server:
            print("\nIMPORTANT: This email will be captured in your Mailtrap inbox, not delivered to the actual address.")
            print("View your test emails at: https://mailtrap.io/inboxes")
        else:
            print(f"Please check your mailbox at: https://www.one-sec-mail.site/mailbox/{recipient_email.split('@')[0]}/")
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        print("\nPossible issues:")
        print("1. Email credentials are incorrect")
        print("2. SMTP server requires different settings")
        print("3. The email provider may block temporary email services")
        print("4. If using Gmail, make sure to enable 'Less secure app access' or use App Password")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a test email to verify email delivery")
    parser.add_argument("--email", default="jjbkdud955@one-sec-mail.site", 
                        help="Email address to send the test to (default: jjbkdud955@one-sec-mail.site)")
    
    args = parser.parse_args()
    
    print("="*50)
    print("Manual Email Test")
    print("="*50)
    
    success = send_test_email(args.email)
    
    if success:
        print("\nTest email sent successfully!")
        if "mailtrap" in os.getenv("SMTP_SERVER", ""):
            print("Check your Mailtrap inbox at: https://mailtrap.io/inboxes")
            print("The email won't be delivered to the external address, it's captured in Mailtrap.")
        else:
            print(f"Please check your mailbox at: https://www.one-sec-mail.site/mailbox/{args.email.split('@')[0]}/")
    else:
        print("\nFailed to send test email. Please check the error messages above.")
    
    print("="*50) 