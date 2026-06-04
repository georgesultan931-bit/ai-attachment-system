from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.notification_list,
        name='notification_list'
    ),

    path(
        'mark-read/',
        views.mark_notifications_read,
        name='mark_notifications_read'
    ),

    path(
        'delete/<int:notification_id>/',
        views.delete_notification,
        name='delete_notification'
    ),

    path(
        'clear-all/',
        views.clear_all_notifications,
        name='clear_all_notifications'
    ),

]