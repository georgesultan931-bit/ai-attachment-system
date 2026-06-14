from django.contrib import admin
from django.urls import path, include, re_path

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from accounts import views as account_views


urlpatterns = [

    
path('password-reset/', account_views.password_reset_request, name='password_reset'),
path('password-reset/done/', account_views.password_reset_done, name='password_reset_done'),
path('reset-password/<uidb64>/<token>/', account_views.password_reset_confirm, name='password_reset_confirm'),
path('reset/<uidb64>/<token>/', account_views.password_reset_confirm, name='password_reset_confirm_legacy'),
path('reset/done/', account_views.password_reset_complete, name='password_reset_complete'),

    path('admin/', admin.site.urls),

    path('', include('accounts.urls')),

    path('', include('students.urls')),

    path('', include('employers.urls')),

    path('', include('internships.urls')),

    path(
        'notifications/',
        include('notifications.urls')
    ),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
elif getattr(settings, "SERVE_MEDIA_FILES", True):
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        ),
    ]

