# licenses/admin.py
from django.contrib import admin
from .models import License, Feature, BusinessFeature


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('license_key', 'tier', 'business',
                    'start_date', 'end_date', 'is_active', 'days_remaining')
    list_filter = ('tier', 'is_active', 'payment_method')
    search_fields = ('license_key', 'business__name')
    readonly_fields = ('created_at', 'updated_at', 'days_remaining_display')

    def days_remaining_display(self, obj):
        return obj.days_remaining
    days_remaining_display.short_description = 'Days Remaining'


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'display_order', 'is_premium')
    list_filter = ('category', 'is_premium')
    search_fields = ('name', 'code', 'description')


@admin.register(BusinessFeature)
class BusinessFeatureAdmin(admin.ModelAdmin):
    list_display = ('business', 'feature', 'is_enabled', 'enabled_at')
    list_filter = ('is_enabled', 'feature__category')
    search_fields = ('business__name', 'feature__name')
