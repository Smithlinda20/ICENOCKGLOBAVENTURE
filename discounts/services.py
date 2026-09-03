"""
Server-side discount engine.

Nothing here trusts the frontend. Every sale line item is re-priced and
re-discounted here, using ONLY active DiscountRule records configured by
the Owner/Admin. Percentages and amounts are never hard-coded.

Three strategies are supported (selected in core.SystemSettings):

HIGHEST     - Apply the single best-matching tier to the whole quantity.
CUMULATIVE  - Decompose the quantity into chunks against the available
              thresholds (largest usable threshold first), applying each
              chunk's own rate - e.g. with tiers at 10/30/50/100 units,
              a quantity of 145 is evaluated as 100 + 30 + 10 + 5
              (remainder at the base/no-discount tier), each chunk
              priced at its own tier's rate.
BEST_VALID  - Compute both HIGHEST and CUMULATIVE and return whichever
              gives the customer the larger discount.
"""
from decimal import ROUND_HALF_UP, Decimal

from core.models import SystemSettings
from .models import DiscountRule

TWO_PLACES = Decimal("0.01")


def _q(value):
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _highest_tier_discount(unit_type, quantity, unit_price):
    """Pick the single qualifying rule (min_qty <= quantity, quantity within
    max_qty if set) that yields the greatest discount, and apply its rate
    to the FULL quantity."""
    candidates = []
    for rule in DiscountRule.objects.filter(active=True):
        if rule.applies_to(unit_type, quantity):
            candidates.append(rule)
    if not candidates:
        return Decimal("0.00"), None

    best_rule = None
    best_discount = Decimal("0.00")
    for rule in candidates:
        per_unit = rule.discount_per_unit(unit_price)
        total = _q(per_unit * quantity)
        if total > best_discount:
            best_discount = total
            best_rule = rule
    return best_discount, best_rule


def _cumulative_discount(unit_type, quantity, unit_price):
    """Greedy chunk decomposition against configured thresholds."""
    thresholds = list(
        DiscountRule.objects.filter(active=True, min_qty__lte=quantity)
        .filter(models_q_unit(unit_type))
        .order_by("-min_qty")
    )
    remaining = quantity
    total_discount = Decimal("0.00")
    breakdown = []
    used_ids = set()

    while remaining > 0:
        usable = [r for r in thresholds if r.min_qty <= remaining and r.id not in used_ids]
        if not usable:
            usable = [r for r in thresholds if r.min_qty <= remaining]
        if not usable:
            break
        rule = max(usable, key=lambda r: r.min_qty)
        chunk = rule.min_qty if rule.min_qty > 1 else remaining
        chunk = min(chunk, remaining)
        per_unit = rule.discount_per_unit(unit_price)
        chunk_discount = _q(per_unit * chunk)
        total_discount += chunk_discount
        breakdown.append({"rule": rule, "quantity": chunk, "discount": chunk_discount})
        used_ids.add(rule.id)
        remaining -= chunk
        if chunk == 0:
            break

    if remaining > 0:
        breakdown.append({"rule": None, "quantity": remaining, "discount": Decimal("0.00")})

    return _q(total_discount), breakdown


def models_q_unit(unit_type):
    from django.db.models import Q
    return Q(unit_type=unit_type) | Q(unit_type=DiscountRule.UnitType.BOTH)


def calculate_line_discount(unit_type, quantity, unit_price):
    """
    Returns a dict:
        {
          "discount_amount": Decimal,
          "strategy_used": "HIGHEST" | "CUMULATIVE",
          "rule": DiscountRule or None,
          "breakdown": [...] (only for cumulative)
        }
    """
    quantity = int(quantity)
    unit_price = Decimal(unit_price)
    if quantity <= 0:
        return {"discount_amount": Decimal("0.00"), "strategy_used": None, "rule": None, "breakdown": []}

    settings_obj = SystemSettings.load()
    strategy = settings_obj.discount_strategy

    highest_amount, highest_rule = _highest_tier_discount(unit_type, quantity, unit_price)

    if strategy == SystemSettings.Strategy.HIGHEST:
        return {"discount_amount": highest_amount, "strategy_used": "HIGHEST", "rule": highest_rule, "breakdown": []}

    cumulative_amount, breakdown = _cumulative_discount(unit_type, quantity, unit_price)

    if strategy == SystemSettings.Strategy.CUMULATIVE:
        return {"discount_amount": cumulative_amount, "strategy_used": "CUMULATIVE", "rule": None, "breakdown": breakdown}

    # BEST_VALID
    if cumulative_amount >= highest_amount:
        return {"discount_amount": cumulative_amount, "strategy_used": "CUMULATIVE", "rule": None, "breakdown": breakdown}
    return {"discount_amount": highest_amount, "strategy_used": "HIGHEST", "rule": highest_rule, "breakdown": []}


def max_manual_discount_amount(gross_amount):
    settings_obj = SystemSettings.load()
    if not settings_obj.allow_manual_discount:
        return Decimal("0.00")
    return _q((settings_obj.max_manual_discount_percent / 100) * Decimal(gross_amount))
