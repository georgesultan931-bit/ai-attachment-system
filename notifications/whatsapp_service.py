import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import (
    WhatsAppConfiguration,
    WhatsAppLog
)


def get_active_whatsapp_config():

    return WhatsAppConfiguration.objects.filter(
        is_active=True
    ).first()


def normalize_phone_number(phone_number, default_country_code):

    digits = ''.join(
        character
        for character in str(phone_number)
        if character.isdigit()
    )

    if digits.startswith('0'):
        digits = f'{default_country_code}{digits[1:]}'

    if not digits.startswith(default_country_code) and len(digits) <= 10:
        digits = f'{default_country_code}{digits}'

    return digits


def send_whatsapp_template(
    phone_number,
    template_name,
    body_parameters,
    message,
):

    config = get_active_whatsapp_config()

    if config is None:

        return (
            False,
            'No active WhatsApp configuration found.'
        )

    recipient = normalize_phone_number(
        phone_number,
        config.default_country_code
    )

    template = {
        'name': template_name,
        'language': {
            'code': config.language_code
        }
    }

    if body_parameters:

        template['components'] = [
            {
                'type': 'body',
                'parameters': [
                    {
                        'type': 'text',
                        'text': str(parameter)
                    }
                    for parameter in body_parameters
                ]
            }
        ]

    payload = {
        'messaging_product': 'whatsapp',
        'to': recipient,
        'type': 'template',
        'template': template
    }

    request = Request(
        url=f'https://graph.facebook.com/v20.0/{config.phone_number_id}/messages',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {config.access_token}',
            'Content-Type': 'application/json',
        },
        method='POST'
    )

    try:

        with urlopen(request, timeout=60) as response:
            response_message = response.read().decode('utf-8')

        WhatsAppLog.objects.create(
            recipient=recipient,
            template_name=template_name,
            message=message,
            status='sent',
            response_message=response_message
        )

        return (
            True,
            'WhatsApp message sent successfully.'
        )

    except HTTPError as error:

        response_message = error.read().decode('utf-8')

    except URLError as error:

        response_message = str(error.reason)

    except Exception as error:

        response_message = str(error)

    WhatsAppLog.objects.create(
        recipient=recipient,
        template_name=template_name,
        message=message,
        status='failed',
        response_message=response_message
    )

    return (
        False,
        response_message
    )


def send_registration_otp_whatsapp(user, otp):

    config = get_active_whatsapp_config()

    if config is None:

        return (
            False,
            'No active WhatsApp configuration found.'
        )

    if config.registration_template_name == 'hello_world':

        return (
            False,
            'WhatsApp OTP was not sent because hello_world is only a Meta test template and cannot include verification codes. Use an approved registration_otp template.'
        )

    message = (
        f'Your AI Internship verification code is {otp}. '
        f'Do not share this code.'
    )

    body_parameters = [
        otp
    ]

    success, response_message = send_whatsapp_template(
        phone_number=user.phone_number,
        template_name=config.registration_template_name,
        body_parameters=body_parameters,
        message=message
    )

    if success:

        return (
            True,
            'WhatsApp OTP sent successfully.'
        )

    return (
        False,
        response_message
    )
