import os
from types import SimpleNamespace

from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

from .models import (
    EmailConfiguration,
    EmailLog
)


def get_active_email_config():

    config = EmailConfiguration.objects.filter(
        is_active=True
    ).first()

    if config is not None:

        return config

    email_host = os.environ.get('EMAIL_HOST', '').strip()
    email_host_user = os.environ.get('EMAIL_HOST_USER', '').strip()
    email_host_password = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()

    if not all([
        email_host,
        email_host_user,
        email_host_password,
    ]):

        return None

    return SimpleNamespace(
        email_host=email_host,
        email_port=int(os.environ.get('EMAIL_PORT', '587')),
        email_use_tls=os.environ.get(
            'EMAIL_USE_TLS',
            'True'
        ).lower() == 'true',
        email_host_user=email_host_user,
        email_host_password=email_host_password,
        default_from_email=os.environ.get(
            'DEFAULT_FROM_EMAIL',
            email_host_user
        ),
        admin_notification_email=os.environ.get(
            'ADMIN_NOTIFICATION_EMAIL',
            email_host_user
        ),
    )


def build_html_email(
    title,
    message,
    button_text=None,
    button_url=None
):

    button_html = ''

    if button_text and button_url:

        button_html = f"""
        <div style="margin-top:30px;">
            <a href="{button_url}"
               style="
               background:#2563eb;
               color:white;
               padding:14px 24px;
               text-decoration:none;
               border-radius:10px;
               font-weight:700;
               display:inline-block;">
                {button_text}
            </a>
        </div>
        """

    return f"""
    <html>
    <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;">

        <table width="100%" style="background:#f4f7fb;padding:30px 0;">

            <tr>

                <td align="center">

                    <table width="600"
                           style="background:white;border-radius:18px;overflow:hidden;">

                        <tr>

                            <td style="
                                background:#2563eb;
                                color:white;
                                padding:30px;
                                text-align:center;">

                                <h2>
                                    AI Internship & Attachment System
                                </h2>

                                <p>
                                    Smart Recruitment Platform
                                </p>

                            </td>

                        </tr>

                        <tr>

                            <td style="padding:35px;">

                                <h2>{title}</h2>

                                <div style="
                                    white-space:pre-line;
                                    line-height:1.8;
                                    color:#334155;">

                                    {message}

                                </div>

                                {button_html}

                            </td>

                        </tr>

                        <tr>

                            <td style="
                                background:#f8fafc;
                                padding:20px;
                                text-align:center;
                                color:#64748b;">

                                This is an automated message.
                                Please do not reply directly.

                            </td>

                        </tr>

                    </table>

                </td>

            </tr>

        </table>

    </body>
    </html>
    """


def send_system_email(
    subject,
    message,
    recipient_list,
    button_text=None,
    button_url=None
):

    config = get_active_email_config()

    if config is None:

        for recipient in recipient_list:

            EmailLog.objects.create(
                recipient=recipient,
                subject=subject,
                message=message,
                status='failed',
                error_message='No active email configuration found.'
            )

        return (
            False,
            'No active email configuration found.'
        )

    try:

        connection = get_connection(
            host=config.email_host,
            port=config.email_port,
            username=config.email_host_user,
            password=config.email_host_password,
            use_tls=config.email_use_tls,
            timeout=60,
        )

        html_content = build_html_email(
            title=subject,
            message=message,
            button_text=button_text,
            button_url=button_url
        )

        text_content = strip_tags(
            html_content
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=config.default_from_email,
            to=recipient_list,
            connection=connection,
        )

        email.attach_alternative(
            html_content,
            "text/html"
        )

        email.send()

        for recipient in recipient_list:

            EmailLog.objects.create(
                recipient=recipient,
                subject=subject,
                message=message,
                status='sent'
            )

        return (
            True,
            'Email sent successfully.'
        )

    except Exception as error:

        for recipient in recipient_list:

            EmailLog.objects.create(
                recipient=recipient,
                subject=subject,
                message=message,
                status='failed',
                error_message=str(error)
            )

        return (
            False,
            str(error)
        )
