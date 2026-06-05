from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from notifications.whatsapp_service import normalize_phone_number

from .models import (
    SMSConfiguration,
    SMSLog
)


def get_active_sms_config():

    return SMSConfiguration.objects.filter(
        is_active=True
    ).first()


def send_sms(phone_number, message):

    config = get_active_sms_config()

    if config is None:

        return (
            False,
            'No active SMS configuration found.'
        )

    recipient = normalize_phone_number(
        phone_number,
        config.default_country_code
    )

    data = {
        'username': config.username,
        'to': f'+{recipient}',
        'message': message,
    }

    if config.sender_id:
        data['from'] = config.sender_id

    request = Request(
        url='https://api.africastalking.com/version1/messaging',
        data=urlencode(data).encode('utf-8'),
        headers={
            'apiKey': config.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST'
    )

    try:

        with urlopen(request, timeout=60) as response:
            response_message = response.read().decode('utf-8')

        SMSLog.objects.create(
            recipient=recipient,
            message=message,
            status='sent',
            response_message=response_message
        )

        return (
            True,
            'SMS OTP sent successfully.'
        )

    except HTTPError as error:

        response_message = error.read().decode('utf-8')

    except URLError as error:

        response_message = str(error.reason)

    except Exception as error:

        response_message = str(error)

    SMSLog.objects.create(
        recipient=recipient,
        message=message,
        status='failed',
        response_message=response_message
    )

    return (
        False,
        response_message
    )


def send_registration_otp_sms(user, otp):

    if not user.phone_number:

        return (
            False,
            'User has no phone number.'
        )

    message = (
        f'Your AI Internship verification code is {otp}. '
        f'Do not share this code. It expires in 15 minutes.'
    )

    return send_sms(
        user.phone_number,
        message
    )
