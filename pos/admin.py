# pos/admin.py
from django.contrib import admin
from .models import Category, Product, Sale, SaleItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'parent', 'display_order', 'is_active')
    list_filter = ('business', 'is_active')
    search_fields = ('name', 'business__name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'business', 'category',
                    'selling_price', 'stock_quantity', 'status', 'is_low_stock')
    list_filter = ('status', 'business', 'category')
    search_fields = ('name', 'sku', 'barcode', 'description')
    readonly_fields = ('created_at', 'updated_at',
                       'profit_margin', 'price_with_tax')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'business', 'total_amount',
                    'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'business')
    search_fields = ('receipt_number', 'transaction_id',
                     'customer_name', 'customer_phone')
    readonly_fields = ('created_at', 'updated_at',
                       'completed_at', 'items_count')


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'unit_price', 'total')
    list_filter = ('sale__business',)
    search_fields = ('product__name', 'sale__receipt_number')
