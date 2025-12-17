# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User model with role-based permissions."""

    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
        BUSINESS_ADMIN = 'BUSINESS_ADMIN', _('Business Admin')
        CASHIER = 'CASHIER', _('Cashier')
        STAFF = 'STAFF', _('Staff')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER,
    )

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )

    # Business association (for non-super admin users)
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    # Additional fields
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(
        max_length=100, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_location = models.CharField(
        max_length=255, blank=True, null=True)

    # License access level (for feature gating)
    license_tier = models.CharField(
        max_length=20,
        choices=[
            ('DEMO', 'Demo'),
            ('BASIC', 'Basic'),
            ('PRO', 'Professional'),
            ('ENTERPRISE', 'Enterprise')
        ],
        default='DEMO'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # FIX: Add custom related_name for groups and user_permissions
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_groups",
        related_query_name="custom_user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="custom_user",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        # Set SUPER_ADMIN users to ENTERPRISE license tier automatically
        if self.role == self.Role.SUPER_ADMIN:
            self.license_tier = 'ENTERPRISE'
        super().save(*args, **kwargs)

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_business_admin(self):
        return self.role == self.Role.BUSINESS_ADMIN

    @property
    def is_cashier(self):
        return self.role == self.Role.CASHIER

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF

    class Meta:
        ordering = ['-date_joined']
        verbose_name = _('User')
        verbose_name_plural = _('Users')
