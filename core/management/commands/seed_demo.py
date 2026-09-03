"""Optional: creates a demo sales rep, a few sample products, and sample
discount rules so you can test the whole workflow immediately after
deployment. Safe to run multiple times (uses get_or_create)."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from discounts.models import DiscountRule
from products.models import Product

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo sales rep, products and discount rules for testing."

    def handle(self, *args, **options):
        rep, created = User.objects.get_or_create(
            username="rep1",
            defaults={"role": User.Role.SALESREP, "first_name": "Demo", "last_name": "Rep"},
        )
        if created:
            rep.set_password("Rep12345")
            rep.save()
            self.stdout.write(self.style.SUCCESS("Created demo sales rep: rep1 / Rep12345"))

        demo_products = [
            {"name": "Indomie Chicken Noodles (Carton)", "sku": "IND-001", "category": "Noodles",
             "pack_price": 500, "carton_price": 9500, "current_stock": 400, "minimum_stock": 30, "packs_per_carton": 20},
            {"name": "Peak Milk Powder Tin", "sku": "PEAK-002", "category": "Dairy",
             "pack_price": 1800, "carton_price": 21000, "current_stock": 250, "minimum_stock": 20, "packs_per_carton": 12},
            {"name": "Golden Penny Semovita", "sku": "GP-003", "category": "Grains",
             "pack_price": 2200, "carton_price": 26000, "current_stock": 150, "minimum_stock": 15, "packs_per_carton": 12},
        ]
        for data in demo_products:
            Product.objects.get_or_create(sku=data["sku"], defaults=data)

        demo_rules = [
            {"name": "Carton 10+", "unit_type": "CARTON", "min_qty": 10, "max_qty": 29, "percentage": 1},
            {"name": "Carton 30+", "unit_type": "CARTON", "min_qty": 30, "max_qty": 49, "percentage": 2},
            {"name": "Carton 50+", "unit_type": "CARTON", "min_qty": 50, "max_qty": 99, "percentage": 3},
            {"name": "Carton 100+", "unit_type": "CARTON", "min_qty": 100, "max_qty": None, "percentage": 5},
        ]
        for data in demo_rules:
            DiscountRule.objects.get_or_create(name=data["name"], defaults=data)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
