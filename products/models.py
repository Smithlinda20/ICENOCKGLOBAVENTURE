from decimal import Decimal

from django.conf import settings
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=40, unique=True)
    category = models.CharField(max_length=80, blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    current_stock = models.PositiveIntegerField(default=0, help_text="Stock is tracked in PACK units.")
    minimum_stock = models.PositiveIntegerField(default=10)

    pack_price = models.DecimalField(max_digits=12, decimal_places=2)
    carton_price = models.DecimalField(max_digits=12, decimal_places=2)
    packs_per_carton = models.PositiveIntegerField(null=True, blank=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock

    def price_for(self, unit_type):
        return self.pack_price if unit_type == "PACK" else self.carton_price


class PriceHistory(models.Model):
    class Field(models.TextChoices):
        PACK_PRICE = "PACK_PRICE", "Pack Price"
        CARTON_PRICE = "CARTON_PRICE", "Carton Price"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    field_changed = models.CharField(max_length=20, choices=Field.choices)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.product.name} {self.field_changed}: {self.old_price} -> {self.new_price}"
