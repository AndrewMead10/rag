import os
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:  # pragma: no cover - boto3 may not be installed in all envs
    boto3 = None
    ClientError = Exception

from ..config import settings


class EmailService:
    def __init__(self):
        self.from_email = settings.ses_from_email or os.getenv('SES_FROM_EMAIL') or ''
        self._enabled = bool(self.from_email and (settings.aws_access_key_id and settings.aws_secret_access_key))
        self._client = None
        if self._enabled and boto3 is not None:
            self._client = boto3.client(
                'ses',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_default_region or 'us-east-1',
            )

    def _build_reset_html(self, reset_url: str) -> str:
        return f"""
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <a href=\"{reset_url}\">Reset Password</a>
        <p>This link will expire in 1 hour.</p>
        """

    def _build_verification_html(self, verification_url: str) -> str:
        return f"""
        <h2>Verify Your Email Address</h2>
        <p>Thank you for registering! Please click the link below to verify your email address:</p>
        <a href=\"{verification_url}\">Verify Email</a>
        <p>This link will expire in 24 hours.</p>
        <p>If you did not create an account, you can safely ignore this email.</p>
        """

    def _build_contact_notification_html(self, name: str, email: str, subject: str, message: str) -> str:
        return f"""
        <h2>New Contact Form Submission</h2>
        <p><strong>From:</strong> {name} ({email})</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Message:</strong></p>
        <p>{message.replace(chr(10), '<br>')}</p>
        <hr>
        <p><em>This message was sent via the contact form on your website.</em></p>
        """

    def _build_contact_confirmation_html(self, name: str) -> str:
        return f"""
        <h2>Thank You for Contacting Us!</h2>
        <p>Hi {name},</p>
        <p>Thank you for reaching out to us. We have received your message and will get back to you within 24-48 hours.</p>
        <p>For your reference, here are the details of your submission:</p>
        <ul>
            <li><strong>Response Time:</strong> 24-48 hours</li>
            <li><strong>Support Email:</strong> support@retriever.sh</li>
            <li><strong>Discord Community:</strong> <a href="https://discord.gg/zqsu7kDSd">Join our Discord</a></li>
        </ul>
        <p>If you have any urgent questions, feel free to join our Discord community or reply directly to this email.</p>
        <p>Best regards,<br>The retriever.sh Team</p>
        """

    def send_password_reset(self, to_email: str, reset_token: str) -> bool:
        reset_url = f"{settings.frontend_url.rstrip('/')}/auth/reset?token={reset_token}"
        subject = "Password Reset Request"
        html_body = self._build_reset_html(reset_url)

        # In non-configured environments, succeed to avoid blocking dev
        if not self._enabled or self._client is None:
            return True

        try:
            self._client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': html_body}},
                },
            )
            return True
        except ClientError as e:  # pragma: no cover
            return False

    def send_email_verification(self, to_email: str, verification_token: str) -> bool:
        verification_url = f"{settings.frontend_url.rstrip('/')}/auth/verify-email?token={verification_token}"
        subject = "Verify Your Email Address"
        html_body = self._build_verification_html(verification_url)

        # In non-configured environments, succeed to avoid blocking dev
        if not self._enabled or self._client is None:
            return True

        try:
            self._client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': html_body}},
                },
            )
            return True
        except ClientError as e:  # pragma: no cover
            return False

    def send_contact_notification(self, name: str, email: str, subject: str, message: str) -> bool:
        """Send notification email to support team about new contact form submission"""
        support_email = "support@retriever.sh"
        email_subject = f"New Contact Form: {subject}"
        html_body = self._build_contact_notification_html(name, email, subject, message)

        # In non-configured environments, succeed to avoid blocking dev
        if not self._enabled or self._client is None:
            return True

        try:
            self._client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [support_email]},
                Message={
                    'Subject': {'Data': email_subject},
                    'Body': {'Html': {'Data': html_body}},
                },
            )
            return True
        except ClientError as e:  # pragma: no cover
            return False

    def send_contact_confirmation(self, to_email: str, name: str) -> bool:
        """Send confirmation email to user who submitted contact form"""
        subject = "Thank you for contacting retriever.sh"
        html_body = self._build_contact_confirmation_html(name)

        # In non-configured environments, succeed to avoid blocking dev
        if not self._enabled or self._client is None:
            return True

        try:
            self._client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': html_body}},
                },
            )
            return True
        except ClientError as e:  # pragma: no cover
            return False


email_service = EmailService()

