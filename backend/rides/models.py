from django.db import models

from accounts.models import (
    CustomerProfile,
    DriverProfile,
    Vehicle,
    VehicleCategory,
)


class Booking(models.Model):

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        SEARCHING = "SEARCHING", "Searching"
        ACCEPTED = "ACCEPTED", "Accepted"
        DRIVER_ARRIVING = "DRIVER_ARRIVING", "Driver Arriving"
        DRIVER_ARRIVED = "DRIVER_ARRIVED", "Driver Arrived"
        STARTED = "STARTED", "Started"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class CancelledBy(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        DRIVER = "DRIVER", "Driver"
        ADMIN = "ADMIN", "Admin"
        SYSTEM = "SYSTEM", "System"

    # Participants
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.PROTECT,
        related_name="bookings",
        null=True,
        blank=True,
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="bookings",
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        VehicleCategory,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    # Pickup
    pickup_address = models.CharField(max_length=500)
    pickup_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
    )
    pickup_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
    )

    # Destination
    destination_address = models.CharField(max_length=500)
    destination_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
    )
    destination_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
    )

    # Trip estimate
    estimated_distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    estimated_duration_minutes = models.PositiveIntegerField()

    # Fare
    estimated_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    final_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Ride OTP
    otp_hash = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    otp_verified = models.BooleanField(default=False)

    # Booking state
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REQUESTED,
    )

    # Cancellation
    cancelled_by = models.CharField(
        max_length=20,
        choices=CancelledBy.choices,
        null=True,
        blank=True,
    )

    cancellation_reason = models.CharField(
        max_length=500,
        blank=True,
    )

    # Lifecycle timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.status}"


class Rating(models.Model):
    class RatingType(models.TextChoices):
        CUSTOMER_TO_DRIVER = "CUSTOMER_TO_DRIVER", "Customer to Driver"
        DRIVER_TO_CUSTOMER = "DRIVER_TO_CUSTOMER", "Driver to Customer"

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    rating_type = models.CharField(
        max_length=25,
        choices=RatingType.choices,
    )
    rating = models.PositiveSmallIntegerField()
    feedback = models.TextField(
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "rating_type"],
                name="unique_booking_rating_per_direction",
            )
        ]

    def __str__(self):
        return f"Rating for Booking #{self.booking_id} ({self.rating_type}): {self.rating}/5"