"""
Email sending service using Resend.
Currently used for email verification codes; will be reused for
password reset emails later.
"""

import resend

from config.settings import settings

resend.api_key = settings.RESEND_API_KEY


def send_verification_email(to_email: str, code: str):
    """
    Sends a 6-digit verification code to the user's email.
    """
    resend.Emails.send({
        "from": "ClipMind AI <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "Verify your ClipMind AI account",
        "html": f"""
            <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
                <h2>Verify your email</h2>
                <p>Your verification code is:</p>
                <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">{code}</p>
                <p>This code expires in 15 minutes.</p>
            </div>
        """,
    })