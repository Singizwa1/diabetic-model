import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.core.config import get_settings
from app.models import Notification, User

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending emails and managing notifications."""
    
    @staticmethod
    def send_high_risk_alert(email: str, user_name: str, probability: float) -> bool:
        """
        Send an email alert for high-risk prediction.
        
        Args:
            email: User email address
            user_name: User's full name
            probability: Prediction probability
        
        Returns:
            True if successful, False otherwise
        """
        try:
            subject = "⚠️ Diabetes Risk Assessment Alert"
            body = f"""
            <html>
                <body>
                    <h2>Diabetes Risk Assessment Alert</h2>
                    <p>Dear {user_name},</p>
                    <p>Your recent diabetes risk assessment has returned a <strong>HIGH RISK</strong> result.</p>
                    <p><strong>Risk Score:</strong> {probability:.1%}</p>
                    <p>This assessment is based on your health profile and reported symptoms over the past few days.</p>
                    <h3>Recommended Actions:</h3>
                    <ul>
                        <li>Schedule a consultation with your healthcare provider</li>
                        <li>Consider lifestyle modifications (diet, exercise)</li>
                        <li>Monitor your symptoms regularly</li>
                        <li>Follow up with another assessment in 1-2 weeks</li>
                    </ul>
                    <p><strong>Important:</strong> This assessment is for informational purposes only and should not replace professional medical advice.</p>
                    <p>Best regards,<br>Diabetes Risk Prediction System</p>
                </body>
            </html>
            """
            
            return EmailService._send_smtp_email(email, subject, body)
        except Exception as e:
            logger.error(f"Error sending high risk alert: {str(e)}")
            return False
    
    @staticmethod
    def send_assessment_complete_notification(email: str, user_name: str) -> bool:
        """
        Send a notification when assessment is complete.
        
        Args:
            email: User email address
            user_name: User's full name
        
        Returns:
            True if successful, False otherwise
        """
        try:
            subject = "Your Diabetes Risk Assessment is Complete"
            body = f"""
            <html>
                <body>
                    <h2>Assessment Complete</h2>
                    <p>Dear {user_name},</p>
                    <p>Your 3-day diabetes risk assessment has been completed.</p>
                    <p>Log in to your account to view your results and risk level.</p>
                    <p>Best regards,<br>Diabetes Risk Prediction System</p>
                </body>
            </html>
            """
            
            return EmailService._send_smtp_email(email, subject, body)
        except Exception as e:
            logger.error(f"Error sending assessment notification: {str(e)}")
            return False

    @staticmethod
    def send_assessment_result_email(
        email: str,
        user_name: str,
        probability: float,
        risk_level: str,
    ) -> bool:
        """Send the completed assessment result with recommendations."""
        risk_value = str(risk_level).lower()

        # Styling for risk level
        color = "green"
        if risk_value == "high":
            color = "red"
        elif risk_value == "medium":
            color = "orange"

        if risk_value == "high":
            subject = "⚠️ High Risk Diabetes Assessment Result"
            recommendation_title = "Recommended Actions"
            recommendations = [
                "Schedule a consultation with your healthcare provider",
                "Review your diet and reduce sugary foods and drinks",
                "Increase regular physical activity if medically appropriate",
                "Monitor your symptoms closely and repeat assessment soon",
            ]
        elif risk_value == "medium":
            subject = "Diabetes Assessment Result - Medium Risk"
            recommendation_title = "Suggested Next Steps"
            recommendations = [
                "Review your diet and hydration habits",
                "Increase daily movement or light exercise",
                "Monitor symptoms over the next few days",
                "Consider booking a follow-up assessment or clinic visit",
            ]
        else:
            subject = "Diabetes Assessment Result - Low Risk"
            recommendation_title = "Maintain These Habits"
            recommendations = [
                "Continue healthy eating habits",
                "Stay physically active",
                "Keep monitoring your health regularly",
                "Repeat the assessment if symptoms change",
            ]

        # Name in bold, risk level colored
        body = f"""
        <html>
            <body>
                <h2>Diabetes Risk Assessment Result</h2>
                <p>Dear <strong>{user_name}</strong>,</p>
                <p>Your 3-day diabetes risk assessment is complete.</p>
                <p><strong>Risk Score:</strong> {probability:.1%}</p>
                <p><strong>Risk Level:</strong> <span style="color:{color}; font-weight:bold">{risk_value.upper()}</span></p>
                <h3>{recommendation_title}</h3>
                <ul>
                    {''.join(f'<li>{item}</li>' for item in recommendations)}
                </ul>
                <p><strong>Important:</strong> This result is informational only and does not replace professional medical advice.</p>
                <p>Best regards,<br>Diabetes Risk Prediction System</p>
            </body>
        </html>
        """

        try:
            return EmailService._send_smtp_email(email, subject, body)
        except Exception as e:
            logger.error(f"Error sending assessment result email: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(email: str, user_name: str, otp_code: str) -> bool:
        """Send a password reset email containing a one-time code (OTP)."""
        try:
            subject = "Password Reset Request"
            body = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>We received a request to reset your password. Use the one-time code below to verify this request. The code expires in 5 minutes.</p>
                    <p><strong style="font-size:20px">{otp_code}</strong></p>
                    <p>If you did not request this, please ignore this email.</p>
                    <p>Best regards,<br>Diabetes Risk Prediction System</p>
                </body>
            </html>
            """

            return EmailService._send_smtp_email(email, subject, body)
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    @staticmethod
    def _send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: Email body in HTML format
        
        Returns:
            True if successful, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email
            
            # Attach HTML part
            part = MIMEText(html_body, "html")
            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP Error: {str(e)}")
            return False
    
    @staticmethod
    def create_in_app_notification(
        db: Session,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str
    ) -> Notification:
        """
        Create an in-app notification.
        
        Args:
            db: Database session
            user_id: User ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
        
        Returns:
            Created notification
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification
    
    @staticmethod
    def mark_notification_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Notification:
        """Mark a notification as read."""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            raise Exception("Notification not found")
        
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        
        return notification
    
    @staticmethod
    def get_user_notifications(db: Session, user_id: UUID, unread_only: bool = False) -> list[Notification]:
        """Get notifications for a user."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).all()
