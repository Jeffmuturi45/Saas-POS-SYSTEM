# reports/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class Report(models.Model):
    """Report model for storing generated reports."""

    class ReportType(models.TextChoices):
        SALES_SUMMARY = 'SALES_SUMMARY', _('Sales Summary')
        INVENTORY = 'INVENTORY', _('Inventory Report')
        STAFF_PERFORMANCE = 'STAFF_PERFORMANCE', _('Staff Performance')
        CUSTOMER = 'CUSTOMER', _('Customer Report')
        FINANCIAL = 'FINANCIAL', _('Financial Report')
        TAX = 'TAX', _('Tax Report')
        CUSTOM = 'CUSTOM', _('Custom Report')

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='reports'
    )

    # Report info
    report_type = models.CharField(
        max_length=50,
        choices=ReportType.choices
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Report parameters (stored as JSON)
    parameters = models.JSONField(default=dict)

    # File storage
    file = models.FileField(
        upload_to='reports/',
        blank=True,
        null=True
    )
    file_format = models.CharField(
        max_length=10,
        choices=[
            ('PDF', 'PDF'),
            ('EXCEL', 'Excel'),
            ('CSV', 'CSV'),
            ('HTML', 'HTML')
        ],
        default='PDF'
    )

    # Scheduling (for automated reports)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('YEARLY', 'Yearly')
        ],
        blank=True,
        null=True
    )
    next_scheduled_run = models.DateTimeField(blank=True, null=True)

    # Audit
    generated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.report_type})"

    @property
    def download_url(self):
        if self.file:
            return self.file.url
        return None

    class Meta:
        ordering = ['-generated_at']
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')


class AuditLog(models.Model):
    """Audit log for tracking important actions."""

    class ActionType(models.TextChoices):
        CREATE = 'CREATE', _('Create')
        UPDATE = 'UPDATE', _('Update')
        DELETE = 'DELETE', _('Delete')
        LOGIN = 'LOGIN', _('Login')
        LOGOUT = 'LOGOUT', _('Logout')
        VIEW = 'VIEW', _('View')
        EXPORT = 'EXPORT', _('Export')
        IMPORT = 'IMPORT', _('Import')
        OTHER = 'OTHER', _('Other')

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True
    )

    # Action details
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices
    )
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)

    # Changes (stored as JSON)
    changes = models.JSONField(default=dict)

    # IP and location
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action_type} {self.model_name} #{self.object_id}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['business', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
