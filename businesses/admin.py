# businesses/admin.py
from django.contrib import admin
from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'status',
                    'email', 'phone', 'created_at')
    list_filter = ('status', 'business_type', 'country', 'is_demo_account')
    search_fields = ('name', 'email', 'phone', 'address')
    readonly_fields = ('created_at', 'updated_at', 'activated_at')

    fieldsets = (
        ('Business Info', {
            'fields': ('name', 'description', 'business_type')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color')
        }),
        ('Settings', {
            'fields': ('currency', 'timezone', 'language', 'date_format')
        }),
        ('Status & License', {
            'fields': ('status', 'license_key', 'subscription_start_date', 'subscription_end_date')
        }),
        ('Demo Settings', {
            'fields': ('is_demo_account', 'demo_expiry_date', 'max_demo_users', 'max_demo_products')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'activated_at')
        }),
    )
