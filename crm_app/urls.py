from django.urls import path
from . import views
from .api_views import get_address_from_location
from .hierarchy_api import update_hierarchy
from .webhook_views import whatsapp_webhook

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('otp-login/', views.otp_login_view, name='otp_login'),
    path('setup-credentials/', views.setup_credentials_view, name='setup_credentials'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-request/', views.create_site_visit_request, name='create_request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('view-requests/', views.view_requests, name='view_requests'),
    path('request/<int:request_id>/', views.request_detail, name='request_detail'),
    path('export-csv/', views.export_requests_csv, name='export_csv'),
    path('upload-users/', views.upload_users_excel, name='upload_users'),
    path('create-user/', views.create_user, name='create_user'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('edit-profile/<int:user_id>/', views.edit_profile, name='edit_user_profile'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('hierarchy-view/', views.hierarchy_view, name='hierarchy_view'),
    path('location-responses/', views.location_responses, name='location_responses'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/get-address/', get_address_from_location, name='get_address_from_location'),
    path('api/update-hierarchy/', update_hierarchy, name='update_hierarchy'),
    path('api/whatsapp-webhook/', whatsapp_webhook, name='whatsapp_webhook'),
]