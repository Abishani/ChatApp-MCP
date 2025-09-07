import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple
import logging

# Try to import SendGrid, but fall back to SMTP if not available
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@example.com')
        
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        if SENDGRID_AVAILABLE and self.sendgrid_api_key:
            return True
        elif self.smtp_username and self.smtp_password:
            return True
        return False
    
    def send_email(self, recipient: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send an email using available service"""
        
        if not self.is_configured():
            return False, "Email service not configured. Please set up SendGrid API key or SMTP credentials."
        
        # Try SendGrid first if available and configured
        if SENDGRID_AVAILABLE and self.sendgrid_api_key:
            return self._send_with_sendgrid(recipient, subject, body)
        
        # Fall back to SMTP
        elif self.smtp_username and self.smtp_password:
            return self._send_with_smtp(recipient, subject, body)
        
        return False, "No email service available"
    
    def _send_with_sendgrid(self, recipient: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send email using SendGrid"""
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=recipient,
                subject=subject,
                html_content=body
            )
            
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True, "Email sent successfully via SendGrid"
            else:
                return False, f"SendGrid error: {response.status_code}"
                
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False, f"SendGrid error: {str(e)}"
    
    def _send_with_smtp(self, recipient: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send email using SMTP with enhanced provider support"""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_email if self.from_email != 'noreply@example.com' else self.smtp_username
            message['To'] = recipient
            
            # Add body (support both HTML and plain text)
            if '<html>' in body.lower() or '<p>' in body.lower():
                html_part = MIMEText(body, 'html')
                message.attach(html_part)
            else:
                text_part = MIMEText(body, 'plain')
                message.attach(text_part)
           
            
            # Send email with enhanced error handling
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                # Handle different authentication methods
                try:
                    server.login(self.smtp_username, self.smtp_password)
                except smtplib.SMTPAuthenticationError as auth_error:
                    if 'gmail' in self.smtp_server.lower():
                        return False, "Gmail authentication failed. Make sure you're using an App Password, not your regular password. Enable 2FA and generate an App Password in your Google Account settings."
                    else:
                        return False, f"Authentication failed for {self.smtp_server}: {str(auth_error)}"
                server.send_message(message)
            
            return True, f"Email sent successfully via {self.smtp_server}"
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False, f"SMTP error: {str(e)}. Check your email credentials and server settings."
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test email service connection"""
        if not self.is_configured():
            return False, "Email service not configured"
        
        # For now, just return configuration status
        if SENDGRID_AVAILABLE and self.sendgrid_api_key:
            return True, "SendGrid configured"
        elif self.smtp_username and self.smtp_password:
            return True, "SMTP configured"
        
        return False, "No email service available"