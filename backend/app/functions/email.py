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


email_service = EmailService()

