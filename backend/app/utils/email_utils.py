"""
Email utilities for sending emails from the application
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from ..config import settings
import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

def get_email_config():
    """Get email configuration from settings"""
    email_config = {
        "smtp_server": settings.SMTP_SERVER,
        "smtp_port": settings.SMTP_PORT,
        "email_sender": settings.EMAIL_SENDER,
        "email_username": settings.EMAIL_USERNAME or settings.EMAIL_SENDER,  # Use EMAIL_USERNAME if available, otherwise use EMAIL_SENDER
        "email_password": settings.EMAIL_PASSWORD,
        "use_tls": settings.EMAIL_USE_TLS
    }
    
    return email_config

def send_email(
    recipient_email: str,
    subject: str,
    text_content: str,
    html_content: str = None,
    email_config: Optional[Dict[str, Any]] = None,
):
    """
    Send an email using the configured email settings.
    
    Args:
        recipient_email: The recipient's email address
        subject: Email subject
        text_content: Plain text content of the email
        html_content: HTML content of the email (optional)
        email_config: Optional dictionary containing email configuration
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if email_config is None:
        email_config = get_email_config()

    try:
        # Create a multipart message and set headers
        message = MIMEMultipart("alternative")
        message["From"] = email_config["email_sender"]
        message["To"] = recipient_email
        message["Subject"] = subject

        # Add body to email
        message.attach(MIMEText(text_content, "plain"))
        if html_content:
            message.attach(MIMEText(html_content, "html"))

        # Log attempt to send email
        logger.info(f"Attempting to send email to {recipient_email}")
        
        # Create secure connection with server and send email
        with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
            if email_config["use_tls"]:
                server.starttls()
            
            # Login to email account
            server.login(email_config["email_username"], email_config["email_password"])
            
            # Send email
            server.sendmail(
                email_config["email_sender"],
                recipient_email,
                message.as_string(),
            )
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def send_license_key_email(recipient_email, license_key, username=None):
    """
    Send an email with a license key to a user.
    
    Args:
        recipient_email: The recipient's email address
        license_key: The license key to send
        username: The username (optional)
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Create the subject
    subject = "Your Language Tutor License Key"
    
    # Create greeting with username if provided
    greeting = f"Dear {username}," if username else "Dear User,"
    
    # Create the email body
    text_content = f"""
{greeting}

Thank you for using Language Tutor! Below is your license key:

{license_key}

Please keep this key safe as you will need it to activate your account.

Best regards,
The Language Tutor Team
"""
    
    html_content = f"""
<html>
  <body>
    <p>{greeting}</p>
    <p>Thank you for using Language Tutor! Below is your license key:</p>
    <div style="background-color: #f5f5f5; padding: 10px; margin: 15px 0; border-left: 4px solid #3498db;">
      <code>{license_key}</code>
    </div>
    <p>Please keep this key safe as you will need it to activate your account.</p>
    <p>Best regards,<br>The Language Tutor Team</p>
  </body>
</html>
"""
    
    # Send the email
    return await asyncio.to_thread(
        send_email,
        recipient_email=recipient_email,
        subject=subject,
        text_content=text_content,
        html_content=html_content
    ) 