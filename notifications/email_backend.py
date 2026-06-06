import ssl
import os

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.utils.functional import cached_property


class LocalSmtpEmailBackend(EmailBackend):

    def __init__(self, *args, allow_insecure_ssl=None, **kwargs):
        self.allow_insecure_ssl = allow_insecure_ssl
        super().__init__(*args, **kwargs)

    @cached_property
    def ssl_context(self):

        allow_insecure_ssl = self.allow_insecure_ssl

        if allow_insecure_ssl is None:
            allow_insecure_ssl = os.environ.get(
                'EMAIL_ALLOW_INSECURE_SMTP_SSL',
                str(getattr(settings, 'EMAIL_ALLOW_INSECURE_SMTP_SSL', False))
            ).lower() == 'true'

        if allow_insecure_ssl:
            return ssl._create_unverified_context()

        return super().ssl_context
