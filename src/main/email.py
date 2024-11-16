from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

# Configure logging for email errors
logger = logging.getLogger(__name__)


def send_email(
    recipients: list,
    subject: str,
    plain_text_message: str,
    html_template: str = None,
    context: dict = None,
):
    """
    Sends an email with optional HTML content.

    Args:
        recipients (list): List of recipient email addresses.
        subject (str): Subject of the email.
        plain_text_message (str): Plain text fallback message.
        html_template (str, optional): Path to the HTML template for the email body.
        context (dict, optional): Context data for rendering the HTML template.

    Returns:
        bool: True if the email is sent successfully, False otherwise.

    Logs:
        Logs any exceptions encountered during email sending.
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = recipients if isinstance(recipients, list) else [recipients]

    try:
        # Initialize the email object
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text_message,
            from_email=from_email,
            to=recipient_list,
        )

        # If an HTML template is provided, render and attach it
        if html_template:
            html_content = render_to_string(html_template, context or {})
            email.attach_alternative(html_content, "text/html")

        # Send the email
        email.send()
        return True
    except Exception as e:
        # Log the error for debugging purposes
        logger.error(f"Failed to send email to {recipient_list}: {e}")
        return False
