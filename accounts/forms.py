from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input", "autofocus": True, "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Password"})
    )


class SalesRepForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank to keep existing password.")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "is_active", "active_staff"]

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user
