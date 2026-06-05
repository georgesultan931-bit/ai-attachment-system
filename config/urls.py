from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views

from accounts.forms import CustomLoginForm


urlpatterns = [

    path('admin/', admin.site.urls),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=CustomLoginForm
        ),
        name='login'
    ),

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
