import ssl

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.utils.functional import cached_property


class LocalSmtpEmailBackend(EmailBackend):

    @cached_property
    def ssl_context(self):

        if getattr(settings, 'EMAIL_ALLOW_INSECURE_SMTP_SSL', False):
            return ssl._create_unverified_context()

        return super().ssl_context
