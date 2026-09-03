"""All stock changes MUST go through record_movement() so every change is
audited and current_stock never drifts out of sync with the movement log."""
from django.db import transaction

from .models import StockMovement


@transaction.atomic
def record_movement(product, movement_type, quantity, user=None, reason="", reference=""):
    """
    quantity: signed integer (positive = stock in, negative = stock out).
    Locks the product row to keep concurrent sales/adjustments consistent.
    """
    from products.models import Product

    locked_product = Product.objects.select_for_update().get(pk=product.pk)
    new_stock = locked_product.current_stock + quantity
    if new_stock < 0:
        raise ValueError(f"Insufficient stock for {locked_product.name}: have {locked_product.current_stock}, need {-quantity}.")
    locked_product.current_stock = new_stock
    locked_product.save(update_fields=["current_stock", "updated_at"])

    movement = StockMovement.objects.create(
        product=locked_product,
        movement_type=movement_type,
        quantity=quantity,
        resulting_stock=new_stock,
        reason=reason,
        user=user,
        reference=reference,
    )
    return movement
