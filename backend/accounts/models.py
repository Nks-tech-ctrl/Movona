from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        DEACTIVATED = "DEACTIVATED", "Deactivated"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)

    is_customer = models.BooleanField(default=True)
    is_driver = models.BooleanField(default=False)

    account_status = models.CharField(
        max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
