# notifications/email_service.py

import os
from email.utils import formataddr, parseaddr
from types import SimpleNamespace

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.defaultfilters import linebreaksbr
from django.utils.html import conditional_escape

from .models import EmailConfiguration, EmailLog


SYSTEM_NAME = 'AI Internship & Attachment System'


def _clean_setting(value):
    """Clean setting value."""
    if value is None:
        return ''
    return str(value).strip()


def _is_certificate_verify_error(error):
    """Check if error is certificate related."""
    return (
        'CERTIFICATE_VERIFY_FAILED' in str(error)
        or 'certificate verify failed' in str(error).lower()
    )


def _sender_name():
    return (
        _clean_setting(os.environ.get('EMAIL_SENDER_NAME'))
        or _clean_setting(getattr(settings, 'EMAIL_SENDER_NAME', ''))
        or SYSTEM_NAME
    )


def _site_url():
    return _clean_setting(getattr(settings, 'PUBLIC_SITE_URL', '')).rstrip('/')


def _extract_email(value):
    cleaned_value = _clean_setting(value)
    return parseaddr(cleaned_value)[1] or cleaned_value


def _uses_google_smtp(config):
    host = _clean_setting(getattr(config, 'email_host', '')).lower()
    return 'gmail.com' in host or 'googlemail.com' in host


def _allow_custom_from():
    return str(
        os.environ.get(
            'EMAIL_ALLOW_CUSTOM_FROM',
            getattr(settings, 'EMAIL_ALLOW_CUSTOM_FROM', False)
        )
    ).strip().lower() in {'1', 'true', 'yes', 'on'}


def _sender_address(config):
    configured_sender = _extract_email(
        getattr(config, 'default_from_email', '')
    )
    smtp_user = _extract_email(
        getattr(config, 'email_host_user', '')
    )

    if _uses_google_smtp(config) and smtp_user and not _allow_custom_from():
        return smtp_user

    return configured_sender or smtp_user


def _display_from_email(config):
    sender = _sender_address(config)
    return formataddr((_sender_name(), sender))


def _reply_to_list(config):
    reply_to = (
        _clean_setting(getattr(config, 'admin_notification_email', ''))
        or _sender_address(config)
    )
    if not reply_to:
        return None
    return [reply_to]


def _build_connection(config, allow_insecure_ssl=False):
    """Build email connection."""
    backend = None
    connection_kwargs = {}
    email_port = int(config.email_port)
    use_tls = bool(getattr(config, 'email_use_tls', False))
    use_ssl = bool(getattr(config, 'email_use_ssl', False))

    if email_port == 587:
        use_tls = True
        use_ssl = False
    elif email_port == 465:
        use_ssl = True
        use_tls = False

    if allow_insecure_ssl:
        backend = 'notifications.email_backend.LocalSmtpEmailBackend'
        connection_kwargs['allow_insecure_ssl'] = allow_insecure_ssl

    return get_connection(
        backend=backend,
        host=config.email_host,
        port=email_port,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=use_tls,
        use_ssl=use_ssl,
        timeout=60,
        **connection_kwargs,
    )


def build_text_email(title, message, button_text=None, button_url=None):
    """Build a clear plain-text fallback for deliverability and accessibility."""
    parts = [
        _clean_setting(title),
        '',
        _clean_setting(message),
    ]

    if button_text and button_url:
        parts.extend(['', f'{_clean_setting(button_text)}: {_clean_setting(button_url)}'])

    site_url = _site_url()
    if site_url:
        parts.extend(['', f'{SYSTEM_NAME}: {site_url}'])

    parts.extend([
        '',
        'This is a transactional notification from AI Internship & Attachment System.',
    ])

    return '\n'.join(part for part in parts if part is not None).strip()


def build_html_email(title, message, button_text=None, button_url=None):
    """Build a simple transactional HTML email."""
    safe_title = conditional_escape(_clean_setting(title))
    safe_message = linebreaksbr(_clean_setting(message))
    site_url = _site_url()
    button_html = ''
    site_html = ''

    if button_text and button_url:
        safe_button_text = conditional_escape(_clean_setting(button_text))
        safe_button_url = conditional_escape(_clean_setting(button_url))
        button_html = f'''
        <div style="margin-top:26px;margin-bottom:10px;">
            <a href="{safe_button_url}"
               style="background:#0f766e;color:#ffffff;padding:13px 20px;text-decoration:none;border-radius:8px;font-weight:700;display:inline-block;">
                {safe_button_text}
            </a>
        </div>
        <p style="margin:10px 0 0;color:#64748b;font-size:13px;line-height:1.5;">
            If the button does not open, copy this link into your browser:<br>
            <a href="{safe_button_url}" style="color:#0f766e;word-break:break-word;">{safe_button_url}</a>
        </p>
        '''

    if site_url:
        safe_site_url = conditional_escape(site_url)
        site_html = f'''
        <p style="margin:8px 0 0;">
            <a href="{safe_site_url}" style="color:#0f766e;text-decoration:none;">{safe_site_url}</a>
        </p>
        '''

    return f'''
    <!doctype html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb;padding:28px 12px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
                        <tr>
                            <td style="background:#102027;color:#ffffff;padding:24px 28px;">
                                <div style="font-size:14px;font-weight:700;letter-spacing:.02em;">{SYSTEM_NAME}</div>
                                <div style="font-size:12px;color:#cbd5e1;margin-top:5px;">Account and application notification</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:30px 28px;">
                                <h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;color:#0f172a;">{safe_title}</h1>
                                <div style="font-size:15px;line-height:1.75;color:#334155;">
                                    {safe_message}
                                </div>
                                {button_html}
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:18px 28px;color:#64748b;font-size:12px;line-height:1.55;">
                                This email was sent because an action happened in your AI Internship &amp; Attachment System account.
                                {site_html}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''


def _send_email_once(config, subject, message, recipient_list, button_text=None, button_url=None, allow_insecure_ssl=False):
    """Send email once."""
    connection = _build_connection(config, allow_insecure_ssl=allow_insecure_ssl)

    html_content = build_html_email(
        title=subject,
        message=message,
        button_text=button_text,
        button_url=button_url,
    )
    text_content = build_text_email(
        title=subject,
        message=message,
        button_text=button_text,
        button_url=button_url,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=_display_from_email(config),
        to=recipient_list,
        connection=connection,
        reply_to=_reply_to_list(config),
        headers={
            'Auto-Submitted': 'auto-generated',
            'X-Auto-Response-Suppress': 'All',
        },
    )

    email.attach_alternative(html_content, 'text/html')
    email.send()


def get_active_email_config():
    """
    Get active email configuration.
    Render/environment settings win over any stale database SMTP row.
    """
    email_host = _clean_setting(
        os.environ.get('EMAIL_HOST')
        or os.environ.get('SMTP_HOST')
        or getattr(settings, 'EMAIL_HOST', '')
    )
    email_host_user = _clean_setting(
        os.environ.get('EMAIL_HOST_USER')
        or os.environ.get('SMTP_USER')
        or os.environ.get('EMAIL_USER')
        or getattr(settings, 'EMAIL_HOST_USER', '')
    )
    email_host_password = _clean_setting(
        os.environ.get('EMAIL_HOST_PASSWORD')
        or os.environ.get('SMTP_PASS')
        or os.environ.get('EMAIL_PASS')
        or getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    )

    if all([email_host, email_host_user, email_host_password]):
        email_port = int(
            os.environ.get('EMAIL_PORT')
            or os.environ.get('SMTP_PORT')
            or getattr(settings, 'EMAIL_PORT', 587)
        )
        email_use_tls = str(
            os.environ.get('EMAIL_USE_TLS', getattr(settings, 'EMAIL_USE_TLS', True))
        ).strip().lower() in {'1', 'true', 'yes', 'on'}
        email_use_ssl = str(
            os.environ.get('EMAIL_USE_SSL', getattr(settings, 'EMAIL_USE_SSL', False))
        ).strip().lower() in {'1', 'true', 'yes', 'on'}

        if email_port == 587:
            email_use_tls = True
            email_use_ssl = False
        elif email_port == 465:
            email_use_ssl = True
            email_use_tls = False

        print(f'Using email config from ENVIRONMENT: {email_host}:{email_port} TLS={email_use_tls} SSL={email_use_ssl}')
        return SimpleNamespace(
            email_host=email_host,
            email_port=email_port,
            email_use_tls=email_use_tls,
            email_use_ssl=email_use_ssl,
            email_host_user=email_host_user,
            email_host_password=email_host_password,
            default_from_email=_clean_setting(
                os.environ.get('DEFAULT_FROM_EMAIL')
                or os.environ.get('EMAIL_FROM')
                or getattr(settings, 'DEFAULT_FROM_EMAIL', '')
                or email_host_user
            ),
            admin_notification_email=_clean_setting(
                os.environ.get('ADMIN_NOTIFICATION_EMAIL')
                or getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '')
                or email_host_user
            ),
            source='ENVIRONMENT',
        )

    try:
        config = EmailConfiguration.objects.filter(is_active=True).first()
        if config:
            if int(config.email_port) == 587 and not config.email_use_tls:
                config.email_use_tls = True
            config.source = 'DATABASE'
            print(f'Using email config from DATABASE: {config.email_host}:{config.email_port} TLS={config.email_use_tls}')
            return config
    except Exception as e:
        print(f'Database email config error (may not exist yet): {e}')

    print('ERROR: No email configuration found in database or environment!')
    return None


def send_system_email(subject, message, recipient_list, button_text=None, button_url=None):
    """
    Send system email with logging and retry on certificate errors.
    """
    config = get_active_email_config()

    if config is None:
        for recipient in recipient_list:
            try:
                EmailLog.objects.create(
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status='failed',
                    error_message='No active email configuration found.',
                )
            except Exception:
                pass
        return False, 'No active email configuration found.'

    try:
        retry_message = ''

        try:
            _send_email_once(
                config,
                subject,
                message,
                recipient_list,
                button_text=button_text,
                button_url=button_url,
            )
        except Exception as first_error:
            if not _is_certificate_verify_error(first_error):
                raise

            retry_message = f' Certificate error, retried with insecure SSL. Original error: {first_error}'
            _send_email_once(
                config,
                subject,
                message,
                recipient_list,
                button_text=button_text,
                button_url=button_url,
                allow_insecure_ssl=True,
            )

        for recipient in recipient_list:
            try:
                EmailLog.objects.create(
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status='sent',
                )
            except Exception:
                pass

        return True, f'Email sent successfully.{retry_message}'

    except Exception as error:
        for recipient in recipient_list:
            try:
                EmailLog.objects.create(
                    recipient=recipient,
                    subject=subject,
                    message=message,
                    status='failed',
                    error_message=str(error),
                )
            except Exception:
                pass

        source = getattr(config, 'source', 'UNKNOWN')
        safe_detail = (
            f'{error} (SMTP source={source}, host={config.email_host}, '
            f'port={config.email_port}, tls={bool(getattr(config, "email_use_tls", False)) or int(config.email_port) == 587}, '
            f'ssl={bool(getattr(config, "email_use_ssl", False)) or int(config.email_port) == 465})'
        )
        return False, safe_detail
