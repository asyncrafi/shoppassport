from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.core.utils.brevo_service import BrevoEmailService

from apps.core.utils.mailgun_service import MailgunEmailService


def send_otp_email(user, otp_code, purpose):
    mailgun_service = MailgunEmailService()

    subject = (
        "Verification Code" if purpose == "verification" else "Password Reset Code"
    )

    context = {
        "user": user,
        "otp": otp_code,
        "purpose": purpose,
        "valid_minutes": 10
    }

    text_content = render_to_string("accounts/otp_email.txt", context)
    html_content = render_to_string("accounts/otp_email.html", context)

    return mailgun_service.send_transactional_email(
        to_email=user.email,
        to_name=user.profile.name,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

# def send_otp_email(user, otp_code, purpose):
#     brevo_service = BrevoEmailService()
#
#     subject = (
#         "Verification Code" if purpose == "verification" else "Password Reset Code"
#     )
#
#     context = {"user": user, "otp": otp_code, "purpose": purpose, "valid_minutes": 10}
#
#     text_content = render_to_string("accounts/otp_email.txt", context)
#     html_content = render_to_string("accounts/otp_email.html", context)
#
#     brevo_service.send_transactional_email(
#         to_email=user.email,
#         to_name=user.profile.name,
#         subject=subject,
#         html_content=html_content,
#         text_content=text_content
#     )

    # def send_otp_email(user, otp_code, purpose):
    #     subject = (
    #         "Verification Code" if purpose == "verification" else "Password Reset Code"
    #     )
    #
    #     context = {"user": user, "otp": otp_code, "purpose": purpose, "valid_minutes": 10}
    #
    #     text_content = render_to_string("accounts/otp_email.txt", context)
    #     html_content = render_to_string("accounts/otp_email.html", context)
    #
    #     email = EmailMultiAlternatives(
    #         subject=subject,
    #         body=text_content,
    #         from_email=settings.DEFAULT_FROM_EMAIL,
    #         to=[user.email],
    #     )
    #     email.attach_alternative(html_content, "text/html")
    #     email.send()