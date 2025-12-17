# accounts/urls.py (update with new endpoints)
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Business registration by super admin
    path('register-business/', views.business_registration_view,
         name='register_business'),

    # Super Admin Management
    path('dashboard/super-admin/', views.super_admin_dashboard,
         name='super_admin_dashboard'),
    path('super-admin/businesses/',
         views.manage_businesses, name='manage_businesses'),
    path('super-admin/business/<int:business_id>/',
         views.business_detail_view, name='business_detail'),
    path('super-admin/business/<int:business_id>/edit/',
         views.edit_business_view, name='edit_business'),
    path('super-admin/users/', views.manage_users, name='manage_users'),
    path('super-admin/licenses/', views.manage_licenses, name='manage_licenses'),
    path('super-admin/analytics/', views.analytics_view, name='analytics_view'),
    path('super-admin/system-settings/',
         views.system_settings_view, name='system_settings'),
    path('super-admin/themes/', views.theme_customization,
         name='theme_customization'),
    path('super-admin/notifications/',
         views.notifications_view, name='notifications_view'),

    # API Endpoints for business actions
    path('api/renew-license/', views.renew_license_view, name='renew_license_api'),
    path('api/suspend-business/', views.suspend_business_view,
         name='suspend_business_api'),
    path('api/activate-business/', views.activate_business_view,
         name='activate_business_api'),
    path('api/delete-business/', views.delete_business_view,
         name='delete_business_api'),

    # User Management API Endpoints
    path('api/user/create/', views.create_user_view, name='create_user_api'),
    path('api/user/<int:user_id>/', views.get_user_view, name='get_user_api'),
    path('api/user/<int:user_id>/update/',
         views.update_user_view, name='update_user_api'),
    path('api/user/<int:user_id>/deactivate/',
         views.deactivate_user_view, name='deactivate_user_api'),
    path('api/user/<int:user_id>/activate/',
         views.activate_user_view, name='activate_user_api'),
    path('api/user/<int:user_id>/reset-password/',
         views.reset_password_view, name='reset_password_api'),
    path('api/user/<int:user_id>/delete/',
         views.delete_user_view, name='delete_user_api'),

    # Analytics API Endpoints
    path('api/analytics/revenue/', views.revenue_analytics_api,
         name='revenue_analytics_api'),
    path('api/analytics/export/', views.export_analytics_api,
         name='export_analytics_api'),

    # Notification API Endpoints
    path('api/notification/<int:notification_id>/mark-read/',
         views.mark_notification_read_view, name='mark_notification_read'),
    path('api/notification/<int:notification_id>/delete/',
         views.delete_notification_view, name='delete_notification'),
    path('api/notifications/mark-all-read/',
         views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    path('api/notifications/clear-all/',
         views.clear_all_notifications_view, name='clear_all_notifications'),

    # Dashboard routes
    path('dashboard/business-admin/', views.business_admin_dashboard,
         name='business_admin_dashboard'),
    path('dashboard/cashier/', views.cashier_dashboard, name='cashier_dashboard'),
]
