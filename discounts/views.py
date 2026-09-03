from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from audit.utils import log_action
from core.models import SystemSettings
from .forms import DiscountRuleForm
from .models import DiscountRule


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@user_passes_test(_is_admin)
def rule_list(request):
    rules = DiscountRule.objects.all()
    settings_obj = SystemSettings.load()
    return render(request, "admin_dash/discounts_list.html", {"rules": rules, "settings_obj": settings_obj})


@user_passes_test(_is_admin)
def rule_edit(request, pk=None):
    instance = get_object_or_404(DiscountRule, pk=pk) if pk else None
    if request.method == "POST":
        form = DiscountRuleForm(request.POST, instance=instance)
        if form.is_valid():
            rule = form.save()
            log_action(request.user, "DISCOUNT_CHANGE", f"Saved discount rule '{rule.name}'")
            messages.success(request, f"Discount rule '{rule.name}' saved.")
            return redirect("discounts:list")
    else:
        form = DiscountRuleForm(instance=instance)
    return render(request, "admin_dash/discount_form.html", {"form": form, "instance": instance})


@user_passes_test(_is_admin)
def rule_toggle(request, pk):
    rule = get_object_or_404(DiscountRule, pk=pk)
    rule.active = not rule.active
    rule.save(update_fields=["active"])
    log_action(request.user, "DISCOUNT_CHANGE", f"{'Activated' if rule.active else 'Deactivated'} rule '{rule.name}'")
    return redirect("discounts:list")


@user_passes_test(_is_admin)
def strategy_settings(request):
    settings_obj = SystemSettings.load()
    if request.method == "POST":
        settings_obj.discount_strategy = request.POST.get("discount_strategy", settings_obj.discount_strategy)
        settings_obj.allow_manual_discount = request.POST.get("allow_manual_discount") == "on"
        try:
            settings_obj.max_manual_discount_percent = request.POST.get("max_manual_discount_percent") or 0
        except (TypeError, ValueError):
            pass
        settings_obj.save()
        log_action(request.user, "DISCOUNT_CHANGE", "Updated discount strategy / manual discount settings")
        messages.success(request, "Discount settings updated.")
        return redirect("discounts:list")
    return redirect("discounts:list")
