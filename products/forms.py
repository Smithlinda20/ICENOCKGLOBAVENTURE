from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "sku", "category", "image",
            "pack_price", "carton_price", "packs_per_carton",
            "current_stock", "minimum_stock", "active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "sku": forms.TextInput(attrs={"class": "input"}),
            "category": forms.TextInput(attrs={"class": "input"}),
            "pack_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "carton_price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "packs_per_carton": forms.NumberInput(attrs={"class": "input"}),
            "current_stock": forms.NumberInput(attrs={"class": "input"}),
            "minimum_stock": forms.NumberInput(attrs={"class": "input"}),
        }
