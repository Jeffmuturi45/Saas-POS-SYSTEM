# pos/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Category(models.Model):
    """Product category model."""

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color
    icon = models.CharField(
        max_length=50, default='fa-box')  # FontAwesome icon

    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['display_order', 'name']
        unique_together = ['business', 'name']


class Product(models.Model):
    """Product/Item model for POS."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        OUT_OF_STOCK = 'OUT_OF_STOCK', _('Out of Stock')
        DISCONTINUED = 'DISCONTINUED', _('Discontinued')

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='products'
    )

    # Basic info
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tax rate in percentage"
    )

    # Inventory
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    track_inventory = models.BooleanField(default=True)

    # Product details
    # kg, pcs, liter, etc.
    unit = models.CharField(max_length=20, default='pcs')
    weight = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True)
    dimensions = models.CharField(
        max_length=100, blank=True, null=True)  # "10x5x2 cm"

    # Images
    primary_image = models.ImageField(
        upload_to='product_images/',
        blank=True,
        null=True
    )
    additional_images = models.JSONField(
        default=list,
        blank=True,
        help_text="List of additional image URLs"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Audit
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def tax_amount(self):
        """Calculate tax amount for one unit."""
        return (self.selling_price * self.tax_rate) / Decimal('100')

    @property
    def price_with_tax(self):
        """Calculate price including tax."""
        return self.selling_price + self.tax_amount

    @property
    def is_low_stock(self):
        """Check if product is low in stock."""
        return self.track_inventory and self.stock_quantity <= self.low_stock_threshold

    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.cost_price == 0:
            return Decimal('100')
        return ((self.selling_price - self.cost_price) / self.cost_price) * Decimal('100')

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
        ]


class Sale(models.Model):
    """Sales transaction model."""

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Cash')
        CARD = 'CARD', _('Credit/Debit Card')
        MPESA = 'MPESA', _('M-PESA')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
        CHEQUE = 'CHEQUE', _('Cheque')
        OTHER = 'OTHER', _('Other')

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', _('Completed')
        PENDING = 'PENDING', _('Pending')
        CANCELLED = 'CANCELLED', _('Cancelled')
        REFUNDED = 'REFUNDED', _('Refunded')

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='sales'
    )

    # Transaction info
    transaction_id = models.CharField(max_length=50, unique=True)
    receipt_number = models.CharField(max_length=50, unique=True)

    # Customer info (could be extended to a Customer model)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)

    # Payment details
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    change_given = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED
    )

    # Staff info
    cashier = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_made'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Sale #{self.receipt_number} - {self.total_amount}"

    @property
    def is_paid(self):
        return self.amount_paid >= self.total_amount

    @property
    def items_count(self):
        return self.items.count()

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Sale')
        verbose_name_plural = _('Sales')
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['receipt_number']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]


class SaleItem(models.Model):
    """Individual items within a sale."""

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items'
    )

    # Item details
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)

    # Calculated fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Calculate amounts before saving
        self.subtotal = self.unit_price * self.quantity
        self.discount_amount = (
            self.subtotal * self.discount_percentage) / Decimal('100')
        discounted_subtotal = self.subtotal - self.discount_amount
        self.tax_amount = (discounted_subtotal *
                           self.tax_rate) / Decimal('100')
        self.total = discounted_subtotal + self.tax_amount

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Sale Item')
        verbose_name_plural = _('Sale Items')
