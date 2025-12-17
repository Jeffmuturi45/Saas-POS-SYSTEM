# superadmin/models.py (update)
from django.db import models
from django.utils.translation import gettext_lazy as _
import json


class Notification(models.Model):
    """System-wide notifications."""

    class NotificationType(models.TextChoices):
        INFO = 'INFO', _('Information')
        WARNING = 'WARNING', _('Warning')
        ERROR = 'ERROR', _('Error')
        SUCCESS = 'SUCCESS', _('Success')
        LICENSE = 'LICENSE', _('License')
        PAYMENT = 'PAYMENT', _('Payment')
        SECURITY = 'SECURITY', _('Security')
        BUSINESS = 'BUSINESS', _('Business')
        USER = 'USER', _('User')

    class Audience(models.TextChoices):
        ALL = 'ALL', _('All Users')
        SUPER_ADMINS = 'SUPER_ADMINS', _('Super Admins Only')
        BUSINESS_ADMINS = 'BUSINESS_ADMINS', _('Business Admins Only')
        CASHIERS = 'CASHIERS', _('Cashiers Only')
        SPECIFIC_BUSINESS = 'SPECIFIC_BUSINESS', _('Specific Business')

    # Notification details
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    audience = models.CharField(
        max_length=50,
        choices=Audience.choices,
        default=Audience.ALL
    )

    # Target specific business if needed
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Data payload (for actions)
    data = models.JSONField(default=dict, blank=True)

    # Scheduling
    scheduled_for = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)

    # Action link
    action_url = models.CharField(max_length=500, blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True, null=True)

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.notification_type})"

    @property
    def get_icon(self):
        """Get icon based on notification type."""
        icon_map = {
            'INFO': 'fa-info-circle',
            'WARNING': 'fa-exclamation-triangle',
            'ERROR': 'fa-exclamation-circle',
            'SUCCESS': 'fa-check-circle',
            'LICENSE': 'fa-key',
            'PAYMENT': 'fa-credit-card',
            'SECURITY': 'fa-shield-alt',
            'BUSINESS': 'fa-building',
            'USER': 'fa-user',
        }
        return icon_map.get(self.notification_type, 'fa-bell')

    @property
    def get_color(self):
        """Get color based on notification type."""
        color_map = {
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'danger',
            'SUCCESS': 'success',
            'LICENSE': 'primary',
            'PAYMENT': 'success',
            'SECURITY': 'danger',
            'BUSINESS': 'primary',
            'USER': 'info',
        }
        return color_map.get(self.notification_type, 'secondary')

    @property
    def is_expired(self):
        from django.utils import timezone
        if self.expires_at:
            return self.expires_at < timezone.now()
        return False

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')


class UserNotification(models.Model):
    """User-specific notification status."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"

    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    class Meta:
        unique_together = ['user', 'notification']
        verbose_name = _('User Notification')
        verbose_name_plural = _('User Notifications')


class SystemActivity(models.Model):
    """System activities/audit log."""

    class ActivityType(models.TextChoices):
        BUSINESS_CREATED = 'BUSINESS_CREATED', _('Business Created')
        BUSINESS_UPDATED = 'BUSINESS_UPDATED', _('Business Updated')
        BUSINESS_SUSPENDED = 'BUSINESS_SUSPENDED', _('Business Suspended')
        BUSINESS_ACTIVATED = 'BUSINESS_ACTIVATED', _('Business Activated')
        BUSINESS_DELETED = 'BUSINESS_DELETED', _('Business Deleted')
        LICENSE_CREATED = 'LICENSE_CREATED', _('License Created')
        LICENSE_RENEWED = 'LICENSE_RENEWED', _('License Renewed')
        LICENSE_EXPIRED = 'LICENSE_EXPIRED', _('License Expired')
        USER_CREATED = 'USER_CREATED', _('User Created')
        USER_UPDATED = 'USER_UPDATED', _('User Updated')
        USER_DELETED = 'USER_DELETED', _('User Deleted')
        LOGIN = 'LOGIN', _('User Login')
        LOGOUT = 'LOGOUT', _('User Logout')
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _('Payment Received')
        PAYMENT_FAILED = 'PAYMENT_FAILED', _('Payment Failed')
        SYSTEM_BACKUP = 'SYSTEM_BACKUP', _('System Backup')
        SYSTEM_UPDATE = 'SYSTEM_UPDATE', _('System Update')
        OTHER = 'OTHER', _('Other')

    activity_type = models.CharField(
        max_length=50, choices=ActivityType.choices)
    description = models.TextField()

    # Related objects
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_activities'
    )

    # Data
    data = models.JSONField(default=dict, blank=True)

    # IP and location
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.activity_type} - {self.description[:50]}..."

    @property
    def icon(self):
        """Get icon based on activity type."""
        icon_map = {
            'BUSINESS_CREATED': 'fa-building',
            'BUSINESS_UPDATED': 'fa-edit',
            'BUSINESS_SUSPENDED': 'fa-pause',
            'BUSINESS_ACTIVATED': 'fa-play',
            'BUSINESS_DELETED': 'fa-trash',
            'LICENSE_CREATED': 'fa-key',
            'LICENSE_RENEWED': 'fa-sync',
            'LICENSE_EXPIRED': 'fa-clock',
            'USER_CREATED': 'fa-user-plus',
            'USER_UPDATED': 'fa-user-edit',
            'USER_DELETED': 'fa-user-minus',
            'LOGIN': 'fa-sign-in-alt',
            'LOGOUT': 'fa-sign-out-alt',
            'PAYMENT_RECEIVED': 'fa-money-bill-wave',
            'PAYMENT_FAILED': 'fa-exclamation-triangle',
            'SYSTEM_BACKUP': 'fa-hdd',
            'SYSTEM_UPDATE': 'fa-cog',
            'OTHER': 'fa-info-circle',
        }
        return icon_map.get(self.activity_type, 'fa-info-circle')

    @property
    def color(self):
        """Get color based on activity type."""
        color_map = {
            'BUSINESS_CREATED': 'success',
            'BUSINESS_UPDATED': 'info',
            'BUSINESS_SUSPENDED': 'warning',
            'BUSINESS_ACTIVATED': 'success',
            'BUSINESS_DELETED': 'danger',
            'LICENSE_CREATED': 'primary',
            'LICENSE_RENEWED': 'success',
            'LICENSE_EXPIRED': 'warning',
            'USER_CREATED': 'success',
            'USER_UPDATED': 'info',
            'USER_DELETED': 'danger',
            'LOGIN': 'info',
            'LOGOUT': 'secondary',
            'PAYMENT_RECEIVED': 'success',
            'PAYMENT_FAILED': 'danger',
            'SYSTEM_BACKUP': 'info',
            'SYSTEM_UPDATE': 'warning',
            'OTHER': 'secondary',
        }
        return color_map.get(self.activity_type, 'secondary')

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('System Activity')
        verbose_name_plural = _('System Activities')
