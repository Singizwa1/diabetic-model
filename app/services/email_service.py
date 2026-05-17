import resend
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import BackgroundTasks
import logging

from app.core.config import get_settings
from app.models import Notification, User

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for sending emails and managing notifications."""

    # ==================== PRIVATE SEND METHOD ====================

    @staticmethod
    def _send_email(to_email: str, subject: str, html_body: str) -> bool:
        """
        Send email — tries Resend first, falls back to SMTP SSL (port 465).

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: Email body in HTML format

        Returns:
            True if successful, False otherwise
        """
        # --- Try Resend first ---
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.EMAIL_FROM,
                "to": to_email,
                "subject": subject,
                "html": html_body,
            })
            logger.info(f"✅ Email sent via Resend to {to_email}")
            return True
        except Exception as resend_error:
            logger.warning(f"⚠️ Resend failed: {str(resend_error)} — trying SMTP SSL...")

        # --- Fallback: Gmail SMTP SSL port 465 ---
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            with smtplib.SMTP_SSL(settings.EMAIL_HOST, 465) as server:
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())

            logger.info(f"✅ Email sent via SMTP SSL to {to_email}")
            return True
        except Exception as smtp_error:
            logger.error(f"❌ SMTP SSL also failed: {str(smtp_error)}")
            return False

    # ==================== BACKGROUND TASK WRAPPERS ====================

    @staticmethod
    def send_high_risk_alert_background(
        background_tasks: BackgroundTasks,
        email: str,
        user_name: str,
        probability: float,
    ) -> None:
        """Schedule high risk alert email as a background task."""
        background_tasks.add_task(
            EmailService.send_high_risk_alert,
            email,
            user_name,
            probability,
        )

    @staticmethod
    def send_assessment_complete_background(
        background_tasks: BackgroundTasks,
        email: str,
        user_name: str,
    ) -> None:
        """Schedule assessment complete email as a background task."""
        background_tasks.add_task(
            EmailService.send_assessment_complete_notification,
            email,
            user_name,
        )

    @staticmethod
    def send_assessment_result_background(
        background_tasks: BackgroundTasks,
        email: str,
        user_name: str,
        probability: float,
        risk_level: str,
    ) -> None:
        """Schedule assessment result email as a background task."""
        background_tasks.add_task(
            EmailService.send_assessment_result_email,
            email,
            user_name,
            probability,
            risk_level,
        )

    @staticmethod
    def send_password_reset_background(
        background_tasks: BackgroundTasks,
        email: str,
        user_name: str,
        otp_code: str,
    ) -> None:
        """Schedule password reset email as a background task."""
        background_tasks.add_task(
            EmailService.send_password_reset_email,
            email,
            user_name,
            otp_code,
        )

    # ==================== EMAIL SENDERS ====================

    @staticmethod
    def send_high_risk_alert(email: str, user_name: str, probability: float) -> bool:
        """Send an email alert for high-risk prediction."""
        try:
            subject = "⚠️ Diabetes Risk Assessment Alert"
            body = f"""
            <html>
                <body>
                    <h2>Diabetes Risk Assessment Alert</h2>
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>Your recent diabetes risk assessment has returned a <strong style="color:red">HIGH RISK</strong> result.</p>
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
            return EmailService._send_email(email, subject, body)
        except Exception as e:
            logger.error(f"Error sending high risk alert: {str(e)}")
            return False

    @staticmethod
    def send_assessment_complete_notification(email: str, user_name: str) -> bool:
        """Send a notification when assessment is complete."""
        try:
            subject = "Your Diabetes Risk Assessment is Complete"
            body = f"""
            <html>
                <body>
                    <h2>Assessment Complete</h2>
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>Your 3-day diabetes risk assessment has been completed.</p>
                    <p>Log in to your account to view your results and risk level.</p>
                    <p>Best regards,<br>Diabetes Risk Prediction System</p>
                </body>
            </html>
            """
            return EmailService._send_email(email, subject, body)
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
            return EmailService._send_email(email, subject, body)
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
                    <p><strong style="font-size:24px; letter-spacing:4px">{otp_code}</strong></p>
                    <p>If you did not request this, please ignore this email.</p>
                    <p>Best regards,<br>Diabetes Risk Prediction System</p>
                </body>
            </html>
            """
            return EmailService._send_email(email, subject, body)
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False

    # ==================== IN-APP NOTIFICATIONS ====================

    @staticmethod
    def create_in_app_notification(
        db: Session,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str,
    ) -> Notification:
        """Create an in-app notification."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def mark_notification_as_read(
        db: Session, notification_id: UUID, user_id: UUID
    ) -> Notification:
        """Mark a notification as read."""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()

        if not notification:
            raise Exception("Notification not found")

        notification.is_read = True
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def get_user_notifications(
        db: Session, user_id: UUID, unread_only: bool = False
    ) -> list[Notification]:
        """Get notifications for a user."""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(Notification.created_at.desc()).all()