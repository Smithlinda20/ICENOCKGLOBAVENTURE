from django.conf import settings
from django.db import models

from products.models import Product


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        OPENING = "OPENING", "Opening Stock"
        IN = "IN", "Stock Received"
        SOLD = "SOLD", "Sold"
        RETURN = "RETURN", "Return"
        ADJUSTMENT = "ADJUSTMENT", "Manual Adjustment"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_movements")
    movement_type = models.CharField(max_length=12, choices=MovementType.choices)
    quantity = models.IntegerField(help_text="Positive for additions, negative for reductions (in PACK units).")
    resulting_stock = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=50, blank=True, help_text="e.g. related receipt number.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name}: {self.movement_type} {self.quantity:+d}"
