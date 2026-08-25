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

class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )

    profile_photo = models.ImageField(
        upload_to="customers/profile/",
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    total_rides = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.user.username} - Customer"


class DriverProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class AvailabilityStatus(models.TextChoices):
        OFFLINE = "OFFLINE", "Offline"
        ONLINE = "ONLINE", "Online"
        BUSY = "BUSY", "Busy"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="driver_profile"
    )

    profile_photo = models.ImageField(
        upload_to="drivers/profile/"
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )

    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.OFFLINE
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    completed_rides = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.user.username} - Driver"