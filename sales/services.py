"""
Server-side sale processing. This is the single source of truth for
prices, discounts and totals - the frontend cart is only ever a
convenience UI. Every number here is recomputed from the database.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from audit.utils import log_action
from discounts.services import calculate_line_discount, max_manual_discount_amount
from inventory.services import record_movement
from products.models import Product

from .models import Sale, SaleItem, generate_receipt_number

TWO_PLACES = Decimal("0.01")


class SaleValidationError(Exception):
    pass


def _q(value):
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@transaction.atomic
def complete_sale(*, salesperson, cart_items, customer_name, customer_phone,
                   payment_method, amount_paid, manual_discount_amount=Decimal("0"),
                   manual_discount_reason=""):
    """
    cart_items: list of dicts: {"product_id": int, "unit_type": "PACK"|"CARTON", "quantity": int}
    Returns the created Sale instance.
    Raises SaleValidationError with a user-facing message on any problem.
    """
    if not cart_items:
        raise SaleValidationError("Cart is empty - add at least one product.")

    sale = Sale(
        salesperson=salesperson,
        customer_name=customer_name or "",
        customer_phone=customer_phone or "",
        payment_method=payment_method,
        manual_discount_reason=manual_discount_reason or "",
    )
    # ensure a unique receipt number even under rare collisions
    for _ in range(5):
        candidate = generate_receipt_number()
        if not Sale.objects.filter(receipt_number=candidate).exists():
            sale.receipt_number = candidate
            break

    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")
    line_items = []

    for raw in cart_items:
        try:
            product = Product.objects.select_for_update().get(pk=raw["product_id"], active=True)
        except Product.DoesNotExist:
            raise SaleValidationError("One of the selected products is no longer available.")

        unit_type = raw.get("unit_type")
        if unit_type not in ("PACK", "CARTON"):
            raise SaleValidationError(f"Invalid unit type for {product.name}.")

        try:
            quantity = int(raw.get("quantity", 0))
        except (TypeError, ValueError):
            quantity = 0
        if quantity <= 0:
            raise SaleValidationError(f"Enter a valid quantity for {product.name}.")

        if quantity > product.current_stock:
            raise SaleValidationError(
                f"Insufficient stock for {product.name}: only {product.current_stock} PACK unit(s) available."
            )

        unit_price = product.price_for(unit_type)  # PROTECTED - always from DB, never from the request
        gross = _q(unit_price * quantity)

        result = calculate_line_discount(unit_type, quantity, unit_price)
        line_discount = _q(result["discount_amount"])
        if line_discount > gross:
            line_discount = gross
        net = _q(gross - line_discount)

        subtotal += gross
        discount_total += line_discount

        line_items.append({
            "product": product,
            "unit_type": unit_type,
            "quantity": quantity,
            "unit_price": unit_price,
            "gross_amount": gross,
            "discount_amount": line_discount,
            "net_amount": net,
            "strategy": result["strategy_used"] or "",
        })

    subtotal = _q(subtotal)
    discount_total = _q(discount_total)

    # Manual (rep-entered) discount, capped server-side by admin settings.
    manual_discount_amount = Decimal(manual_discount_amount or 0)
    allowed_manual_cap = max_manual_discount_amount(subtotal - discount_total)
    if manual_discount_amount < 0:
        manual_discount_amount = Decimal("0.00")
    if manual_discount_amount > allowed_manual_cap:
        manual_discount_amount = allowed_manual_cap
    manual_discount_amount = _q(manual_discount_amount)

    total = _q(subtotal - discount_total - manual_discount_amount)
    if total < 0:
        total = Decimal("0.00")

    amount_paid = _q(Decimal(amount_paid or 0))
    balance = _q(amount_paid - total)

    sale.subtotal = subtotal
    sale.discount_total = discount_total
    sale.manual_discount_amount = manual_discount_amount
    sale.total = total
    sale.amount_paid = amount_paid
    sale.balance = balance
    sale.save()

    for li in line_items:
        SaleItem.objects.create(
            sale=sale,
            product=li["product"],
            unit_type=li["unit_type"],
            quantity=li["quantity"],
            unit_price=li["unit_price"],
            gross_amount=li["gross_amount"],
            discount_amount=li["discount_amount"],
            net_amount=li["net_amount"],
            discount_strategy_used=li["strategy"],
        )
        # Stock is tracked in PACK units. A CARTON sale reduces stock by
        # quantity * packs_per_carton when that ratio is configured;
        # otherwise 1 carton reduces stock by 1 unit (lean MVP default).
        product = li["product"]
        if li["unit_type"] == "CARTON" and product.packs_per_carton:
            stock_reduction = li["quantity"] * product.packs_per_carton
        else:
            stock_reduction = li["quantity"]
        record_movement(
            product, "SOLD", -stock_reduction, user=salesperson,
            reason=f"Sale {sale.receipt_number}", reference=sale.receipt_number,
        )

    log_action(salesperson, "SALE_COMPLETED", f"Sale {sale.receipt_number} total \u20a6{total}")
    return sale


@transaction.atomic
def cancel_sale(sale, user, reason=""):
    if sale.status == Sale.Status.CANCELLED:
        return sale
    for item in sale.items.select_related("product"):
        product = item.product
        if item.unit_type == "CARTON" and product.packs_per_carton:
            restock = item.quantity * product.packs_per_carton
        else:
            restock = item.quantity
        record_movement(product, "RETURN", restock, user=user,
                         reason=f"Cancelled sale {sale.receipt_number}: {reason}", reference=sale.receipt_number)
    sale.status = Sale.Status.CANCELLED
    sale.save(update_fields=["status"])
    log_action(user, "SALE_CANCELLED", f"Sale {sale.receipt_number} cancelled: {reason}")
    return sale
