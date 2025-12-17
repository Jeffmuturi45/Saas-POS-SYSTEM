# licenses/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
import secrets
import string


class License(models.Model):
    """License model for subscription management."""

    class Tier(models.TextChoices):
        DEMO = 'DEMO', _('Demo/Trial')
        BASIC = 'BASIC', _('Basic')
        PRO = 'PRO', _('Professional')
        ENTERPRISE = 'ENTERPRISE', _('Enterprise')

    # License details
    license_key = models.CharField(max_length=100, unique=True)
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.DEMO
    )

    # Associated business
    business = models.OneToOneField(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='license'
    )

    # Subscription period
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')

    # License limits
    max_users = models.IntegerField(default=5)
    max_products = models.IntegerField(default=1000)
    max_branches = models.IntegerField(default=1)
    max_storage_mb = models.IntegerField(default=100)

    # Payment info
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('MPESA', 'M-PESA'),
            ('STRIPE', 'Stripe'),
            ('PAYPAL', 'PayPal'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CASH', 'Cash')
        ],
        blank=True,
        null=True
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    last_payment_date = models.DateField(blank=True, null=True)
    next_payment_date = models.DateField(blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.license_key} - {self.tier}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.end_date < timezone.now().date()

    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now().date()).days

    @classmethod
    def generate_license_key(cls):
        """Generate a secure random license key."""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(25))

    def save(self, *args, **kwargs):
        if not self.license_key:
            self.license_key = self.generate_license_key()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('License')
        verbose_name_plural = _('Licenses')


class Feature(models.Model):
    """Feature model for feature gating."""

    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField()

    # Feature availability by tier
    available_in_demo = models.BooleanField(default=False)
    available_in_basic = models.BooleanField(default=False)
    available_in_pro = models.BooleanField(default=False)
    available_in_enterprise = models.BooleanField(default=True)

    # Feature properties
    requires_setup = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    icon = models.CharField(
        max_length=50, default='fa-cog')  # FontAwesome icon

    # Ordering
    display_order = models.IntegerField(default=0)
    category = models.CharField(
        max_length=50,
        choices=[
            ('POS', 'POS Features'),
            ('INVENTORY', 'Inventory Management'),
            ('REPORTING', 'Reporting & Analytics'),
            ('STAFF', 'Staff Management'),
            ('INTEGRATION', 'Integrations'),
            ('SECURITY', 'Security Features'),
            ('OTHER', 'Other Features')
        ],
        default='POS'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_available_in_tier(self, tier):
        """Check if feature is available in given tier."""
        tier_map = {
            'DEMO': self.available_in_demo,
            'BASIC': self.available_in_basic,
            'PRO': self.available_in_pro,
            'ENTERPRISE': self.available_in_enterprise
        }
        return tier_map.get(tier, False)

    class Meta:
        ordering = ['category', 'display_order']
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')


class BusinessFeature(models.Model):
    """Many-to-many relationship between Business and Feature with additional data."""

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='feature_access'
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='business_access'
    )

    # Feature-specific settings
    is_enabled = models.BooleanField(default=True)
    # Feature-specific settings
    settings = models.JSONField(default=dict, blank=True)

    # Access control
    enabled_at = models.DateTimeField(blank=True, null=True)
    enabled_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} - {self.feature.name}"

    class Meta:
        unique_together = ['business', 'feature']
        verbose_name = _('Business Feature')
        verbose_name_plural = _('Business Features')
