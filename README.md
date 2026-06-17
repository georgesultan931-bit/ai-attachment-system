# AI Internship & Attachment Matching System

Django system for student registration, admin verification, employer opportunities, skill matching, applications, interviews, notifications, email OTP, and WhatsApp notification configuration.

## Important

GitHub stores the project code. GitHub Pages cannot run this Django backend because it needs Python, a database, authentication, email, file uploads, and server-side views.

For a public link that works anywhere, push this repository to GitHub, then deploy it from GitHub to a Python hosting provider such as Render, Railway, PythonAnywhere, or a VPS.

## Local Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Environment Variables

Copy `.env.example` into your hosting provider's environment settings and set real values:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
PUBLIC_SITE_URL
DATABASE_URL
DEFAULT_FROM_EMAIL
EMAIL_SENDER_NAME
EMAIL_ALLOW_CUSTOM_FROM
EMAIL_ALLOW_INSECURE_SMTP_SSL
EMAIL_HOST
EMAIL_PORT
EMAIL_USE_TLS
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
ADMIN_NOTIFICATION_EMAIL
```

Email and WhatsApp provider credentials should be configured securely, not committed into GitHub.


## Email Inbox Delivery

To make password reset, verification, chat alerts, and registration emails reach user inboxes more reliably, keep the visible sender aligned with the SMTP login address. When using Gmail SMTP, leave `EMAIL_ALLOW_CUSTOM_FROM=False`; the app will send from `EMAIL_HOST_USER` even if `DEFAULT_FROM_EMAIL` is accidentally different.

For Render with Gmail SMTP, set these email variables:

```text
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=georgesultan931@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=georgesultan931@gmail.com
EMAIL_SENDER_NAME=AI Internship & Attachment System
EMAIL_ALLOW_CUSTOM_FROM=False
ADMIN_NOTIFICATION_EMAIL=georgesultan931@gmail.com
```

Before presenting, send a password reset email to Gmail and use Show original to confirm SPF or DKIM passes. If a test message lands in Spam after changing settings, mark the first valid message as Not spam.

## GitHub Push

After creating an empty GitHub repository, run:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git branch -M main
git push -u origin main
```

## Deployment Notes

Recommended production setup:

- Use PostgreSQL through `DATABASE_URL`.
- Set `DJANGO_DEBUG=False`.
- Set `DJANGO_ALLOWED_HOSTS` to your live domain.
- Set `DJANGO_CSRF_TRUSTED_ORIGINS` to your live HTTPS origin.
- Run migrations on deployment.
- Run collectstatic on deployment.
- Configure email and WhatsApp credentials in the hosting dashboard or admin panel.
- Before presenting, use a verified domain sender and confirm SPF, DKIM, and DMARC pass so email is more likely to reach Inbox.

Do not commit:

- `db.sqlite3`
- `media/`
- `.env`
- `email_service/.env`
- `venv/`
- `node_modules/`
