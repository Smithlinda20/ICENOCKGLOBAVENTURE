from django.db import models


class DiscountRule(models.Model):
    class UnitType(models.TextChoices):
        PACK = "PACK", "Pack"
        CARTON = "CARTON", "Carton"
        BOTH = "BOTH", "Both"

    name = models.CharField(max_length=100, help_text="e.g. 'Carton 10+ tier'")
    unit_type = models.CharField(max_length=6, choices=UnitType.choices, default=UnitType.BOTH)
    min_qty = models.PositiveIntegerField(default=1)
    max_qty = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for no upper limit.")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                      help_text="e.g. 5 for 5%. Leave blank if using a fixed amount instead.")
    fixed_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                        help_text="Fixed discount amount per unit. Leave blank if using percentage.")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["unit_type", "min_qty"]

    def __str__(self):
        rate = f"{self.percentage}%" if self.percentage is not None else f"\u20a6{self.fixed_amount}"
        upper = f"-{self.max_qty}" if self.max_qty else "+"
        return f"{self.name}: {self.unit_type} {self.min_qty}{upper} = {rate}"

    def applies_to(self, unit_type, quantity):
        if self.unit_type != self.UnitType.BOTH and self.unit_type != unit_type:
            return False
        if quantity < self.min_qty:
            return False
        if self.max_qty and quantity > self.max_qty:
            return False
        return True

    def discount_per_unit(self, unit_price):
        if self.percentage is not None:
            return (self.percentage / 100) * unit_price
        if self.fixed_amount is not None:
            return self.fixed_amount
        return 0
