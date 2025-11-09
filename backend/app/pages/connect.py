from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..config import settings
from ..functions.email import email_service

router = APIRouter()

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class ContactResponse(BaseModel):
    success: bool
    message: str

@router.get("/onload", response_model=dict)
async def connect_onload():
    """
    Load connect page data
    """
    return {
        "discord_link": "https://discord.gg/zqsu7kDSd",
        "support_email": "support@retriever.sh",
        "contact_info": {
            "email": "support@retriever.sh",
            "response_time": "24-48 hours"
        }
    }

@router.post("/submit", response_model=ContactResponse)
async def submit_contact_form(form_data: ContactForm):
    """
    Handle contact form submission
    """
    try:
        # 1. Send email notification to support team
        support_notification_sent = email_service.send_contact_notification(
            name=form_data.name,
            email=form_data.email,
            subject=form_data.subject,
            message=form_data.message
        )

        # 2. Send confirmation email to user
        user_confirmation_sent = email_service.send_contact_confirmation(
            to_email=form_data.email,
            name=form_data.name
        )

        # 3. Log the submission for debugging/auditing
        print(f"Contact form submission from {form_data.email}:")
        print(f"Subject: {form_data.subject}")
        print(f"Support notification sent: {support_notification_sent}")
        print(f"User confirmation sent: {user_confirmation_sent}")

        return ContactResponse(
            success=True,
            message="Thank you for your message! We'll get back to you within 24-48 hours."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to submit contact form. Please try again."
        )
