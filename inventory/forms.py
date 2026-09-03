from django import forms

from products.models import Product


class StockAdjustmentForm(forms.Form):
    ADJUST_CHOICES = [("IN", "Add Stock"), ("ADJUSTMENT", "Manual Adjustment (+/-)")]

    product = forms.ModelChoiceField(queryset=Product.objects.filter(active=True), widget=forms.Select(attrs={"class": "input"}))
    movement_type = forms.ChoiceField(choices=ADJUST_CHOICES, widget=forms.Select(attrs={"class": "input"}))
    quantity = forms.IntegerField(help_text="For adjustments, use a negative number to reduce stock.",
                                   widget=forms.NumberInput(attrs={"class": "input"}))
    reason = forms.CharField(required=True, widget=forms.TextInput(attrs={"class": "input"}))
