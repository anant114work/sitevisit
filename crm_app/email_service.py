# crm_app/email_service.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Email SMTP Configuration - Configure with your email provider
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_username"
SMTP_PASSWORD = "your_password"
FROM_EMAIL = "noreply@example.com"
EMAIL_ENABLED = False  # Set to True after configuring

def send_email(to_emails, subject, message, request_id=None):
    """Send email notification using SMTP"""
    print(f"\n=== EMAIL NOTIFICATION TRIGGERED ===")
    print(f"To: {to_emails}")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    print(f"Request ID: {request_id}")
    print(f"Email Enabled: {EMAIL_ENABLED}")
    
    if not EMAIL_ENABLED:
        print("❌ Email sending DISABLED - configure SMTP settings first")
        logger.info("Email sending disabled - configure SMTP settings first")
        return {"ok": True, "results": [{"ok": True, "email": email, "note": "Email disabled"} for email in (to_emails if isinstance(to_emails, list) else [to_emails])]}
    
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    print(f"✅ Attempting to send emails to {len(to_emails)} recipients")
    results = []
    for email in to_emails:
        try:
            print(f"  → Sending to {email}...")
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = FROM_EMAIL
            msg['To'] = email
            msg['Subject'] = subject
            
            # HTML email body
            html_body = f"""
            <html>
            <body>
                <h2>Site Visit Request Notification</h2>
                <p>{message}</p>
                {f'<p><strong>Request ID:</strong> {request_id}</p>' if request_id else ''}
                <p>Please log in to the system to view and approve the request.</p>
                <br>
                <p>Best regards,<br>BOP Realty Team</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send via SMTP
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"  ✅ SUCCESS: Email sent to {email}")
            logger.info(f"Email sent successfully to {email}")
            results.append({"ok": True, "email": email})
            
        except Exception as e:
            print(f"  ❌ ERROR: {email} - Exception: {e}")
            logger.error(f"Email exception for {email}: {e}")
            results.append({"ok": False, "email": email, "error": str(e)})
    
    print(f"=== EMAIL NOTIFICATION COMPLETE ===\n")
    return {"ok": all(r["ok"] for r in results), "results": results}