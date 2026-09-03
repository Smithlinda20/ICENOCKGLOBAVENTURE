from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Owner / Admin"
        SALESREP = "SALESREP", "Sales Representative"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SALESREP)
    phone = models.CharField(max_length=20, blank=True)
    active_staff = models.BooleanField(default=True, help_text="Deactivate to block login without deleting.")

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_salesrep_role(self):
        return self.role == self.Role.SALESREP

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
