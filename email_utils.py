import os
from flask_mail import Mail, Message

mail = Mail()

def init_email(app):
    """Initialize email configuration"""
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@aiattendance.com')
    mail.init_app(app)

def send_contact_email(name, email, subject, organization, message):
    """Send contact form email to admin"""
    try:
        msg = Message(
            subject=f"New Contact Form Submission: {subject}",
            recipients=[os.getenv('ADMIN_EMAIL', 'admin@aiattendance.com')],
            body=f"""
New Contact Form Submission:

Name: {name}
Email: {email}
Organization: {organization}
Subject: {subject}

Message:
{message}

---
Please reply to: {email}
            """,
            html=f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h2 style="margin: 0;">New Contact Form Submission</h2>
        </div>
        
        <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
            <p><strong>Organization:</strong> {organization if organization else 'Not provided'}</p>
            <p><strong>Subject:</strong> {subject}</p>
        </div>
        
        <div style="background: white; padding: 20px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-top: 0;">Message:</h4>
            <p style="white-space: pre-wrap;">{message}</p>
        </div>
        
        <div style="background: #f9f9f9; padding: 15px; border-radius: 10px; font-size: 12px; color: #666;">
            <p>This email was sent from the AI Attendance contact form.</p>
            <p>Reply directly to <strong>{email}</strong> or use the admin panel to respond.</p>
        </div>
    </body>
</html>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_contact_confirmation(name, email):
    """Send confirmation email to user"""
    try:
        msg = Message(
            subject="We received your message - AI Attendance",
            recipients=[email],
            body=f"""
Hello {name},

Thank you for contacting AI Attendance! We have received your message and will get back to you as soon as possible.

Our support team typically responds within:
- Urgent issues: 2-4 hours
- High priority: 4-8 hours  
- General inquiries: 24 hours

Best regards,
AI Attendance Support Team
            """,
            html=f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 28px;">Thank You!</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">We received your message</p>
        </div>
        
        <div style="padding: 20px; background: white;">
            <p>Hello <strong>{name}</strong>,</p>
            
            <p>Thank you for contacting AI Attendance! We have received your message and will get back to you as soon as possible.</p>
            
            <div style="background: #f0f4ff; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h4 style="color: #667eea; margin-top: 0;">Response Times:</h4>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li><strong>Urgent issues:</strong> 2-4 hours</li>
                    <li><strong>High priority:</strong> 4-8 hours</li>
                    <li><strong>General inquiries:</strong> 24 hours</li>
                </ul>
            </div>
            
            <p>If you have any urgent matters, please don't hesitate to call us at <strong>+1 (800) ATTEND-1</strong>.</p>
            
            <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                Best regards,<br>
                <strong>AI Attendance Support Team</strong>
            </p>
        </div>
    </body>
</html>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False
