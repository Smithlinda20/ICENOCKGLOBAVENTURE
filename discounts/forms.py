from django import forms

from .models import DiscountRule


class DiscountRuleForm(forms.ModelForm):
    class Meta:
        model = DiscountRule
        fields = ["name", "unit_type", "min_qty", "max_qty", "percentage", "fixed_amount", "active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "min_qty": forms.NumberInput(attrs={"class": "input"}),
            "max_qty": forms.NumberInput(attrs={"class": "input"}),
            "percentage": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "fixed_amount": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("percentage") and not cleaned.get("fixed_amount"):
            raise forms.ValidationError("Set either a percentage or a fixed discount amount.")
        if cleaned.get("percentage") and cleaned.get("fixed_amount"):
            raise forms.ValidationError("Set only ONE of percentage or fixed amount, not both.")
        return cleaned
