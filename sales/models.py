import random
import string
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


def generate_receipt_number():
    stamp = timezone.localtime().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=5))
    return f"IN-{stamp}-{suffix}"


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        TRANSFER = "TRANSFER", "Bank Transfer"
        POS = "POS", "POS"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    receipt_number = models.CharField(max_length=30, unique=True, default=generate_receipt_number, editable=False)
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales")

    customer_name = models.CharField(max_length=120, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True, help_text="Nigerian phone number, any common format.")

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    manual_discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    manual_discount_reason = models.CharField(max_length=255, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Positive = change due to customer, negative = owed by customer.")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    reprint_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.receipt_number} - \u20a6{self.total}"

    @property
    def whatsapp_international_number(self):
        return normalize_ng_phone(self.customer_phone)


class SaleItem(models.Model):
    class UnitType(models.TextChoices):
        PACK = "PACK", "Pack"
        CARTON = "CARTON", "Carton"

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    unit_type = models.CharField(max_length=6, choices=UnitType.choices)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=14, decimal_places=2)
    discount_strategy_used = models.CharField(max_length=12, blank=True)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} {self.unit_type}"


def normalize_ng_phone(raw):
    """Normalize common Nigerian phone number formats to international
    format without a leading '+', suitable for a wa.me link.
    Examples:
        08033604514      -> 2348033604514
        8033604514       -> 2348033604514
        +2348033604514   -> 2348033604514
        2348033604514    -> 2348033604514
    """
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("234"):
        return digits
    if digits.startswith("0"):
        return "234" + digits[1:]
    if len(digits) == 10:
        return "234" + digits
    return digits
