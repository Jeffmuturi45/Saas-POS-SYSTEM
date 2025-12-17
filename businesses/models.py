# businesses/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class Business(models.Model):
    """Business/Tenant model for multi-tenancy."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        PENDING = 'PENDING', _('Pending Approval')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Business details
    business_type = models.CharField(
        max_length=50,
        choices=[
            ('RETAIL', 'Retail Store'),
            ('RESTAURANT', 'Restaurant'),
            ('SERVICE', 'Service Business'),
            ('WHOLESALE', 'Wholesale'),
            ('OTHER', 'Other')
        ],
        default='RETAIL'
    )

    # Contact information
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = CountryField()
    postal_code = models.CharField(max_length=20)

    # Business branding
    logo = models.ImageField(
        upload_to='business_logos/',
        blank=True,
        null=True
    )
    primary_color = models.CharField(
        max_length=7, default='#4361ee')  # Hex color
    secondary_color = models.CharField(max_length=7, default='#3f37c9')

    # Business settings
    currency = models.CharField(max_length=10, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')

    # Business status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Subscription/license info
    license_key = models.CharField(max_length=100, blank=True, null=True)
    subscription_start_date = models.DateField(blank=True, null=True)
    subscription_end_date = models.DateField(blank=True, null=True)

    # Demo/Trial settings
    is_demo_account = models.BooleanField(default=True)
    demo_expiry_date = models.DateField(blank=True, null=True)
    max_demo_users = models.IntegerField(default=3)
    max_demo_products = models.IntegerField(default=100)

    # Audit fields
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_businesses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.business_type})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def is_demo_active(self):
        from django.utils import timezone
        if not self.is_demo_account:
            return False
        if self.demo_expiry_date and self.demo_expiry_date < timezone.now().date():
            return False
        return True

    @property
    def subscription_status(self):
        from django.utils import timezone
        if not self.license_key:
            return 'NO_LICENSE'
        if self.subscription_end_date and self.subscription_end_date < timezone.now().date():
            return 'EXPIRED'
        return 'ACTIVE'

    class Meta:
        verbose_name = _('Business')
        verbose_name_plural = _('Businesses')
        ordering = ['-created_at']
