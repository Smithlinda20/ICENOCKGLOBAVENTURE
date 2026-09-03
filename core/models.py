from django.core.exceptions import ValidationError
from django.db import models


class SystemSettings(models.Model):
    """Singleton store-wide configuration, editable by the Owner/Admin."""

    class Strategy(models.TextChoices):
        HIGHEST = "HIGHEST", "Highest Applicable Tier"
        CUMULATIVE = "CUMULATIVE", "Cumulative / Tier Decomposition"
        BEST_VALID = "BEST_VALID", "Best Valid Discount (auto-pick best for customer)"

    company_name = models.CharField(max_length=150, default="ICE NOCK GLOBAL VENTURE")
    address = models.CharField(
        max_length=255, default="NO 34 ADO BAYERO PLAZA BAYAJIDDA STREET KADUNA"
    )
    phone = models.CharField(max_length=30, default="08033604514")
    email = models.EmailField(default="abdulazizmohammedbello4@gmail.com")
    receipt_footer = models.CharField(
        max_length=255, default="Thank you for your patronage! Goods sold in good condition are not returnable."
    )
    currency_code = models.CharField(max_length=6, default="NGN")
    currency_symbol = models.CharField(max_length=4, default="\u20a6")
    timezone_name = models.CharField(max_length=64, default="Africa/Lagos")
    thermal_receipt_width_mm = models.PositiveSmallIntegerField(
        choices=[(58, "58mm"), (80, "80mm")], default=80
    )
    low_stock_threshold_default = models.PositiveIntegerField(
        default=10, help_text="Used only for products that don't set their own minimum stock."
    )

    discount_strategy = models.CharField(max_length=12, choices=Strategy.choices, default=Strategy.HIGHEST)
    allow_manual_discount = models.BooleanField(default=True)
    max_manual_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.pk and SystemSettings.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one SystemSettings record may exist.")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Store Settings ({self.company_name})"
