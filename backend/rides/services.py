from decimal import Decimal
import hashlib
import secrets

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from accounts.models import (
    User,
    CustomerProfile,
    DriverProfile,
    VehicleCategory,
    Vehicle,
)

from .models import Booking


def calculate_fare(
    category: VehicleCategory,
    distance_km: Decimal,
    duration_minutes: int,
) -> Decimal:
    """
    Calculate the estimated fare for a ride.

    Formula:
        Base Fare
        + (Distance × Per KM Rate)
        + (Duration × Per Minute Rate)
    """

    distance_charge = distance_km * category.per_km_rate

    time_charge = Decimal(duration_minutes) * category.per_minute_rate

    total_fare = category.base_fare + distance_charge + time_charge

    return total_fare.quantize(Decimal("0.01"))


@transaction.atomic
def create_booking(
    customer: CustomerProfile,
    category: VehicleCategory,
    pickup_address: str,
    pickup_latitude,
    pickup_longitude,
    destination_address: str,
    destination_latitude,
    destination_longitude,
    distance_km,
    duration_minutes: int,
) -> Booking:

    if not category.is_active:
        raise ValidationError("This vehicle category is not available.")

    if distance_km <= 0:
        raise ValidationError("Distance must be greater than zero.")

    if duration_minutes <= 0:
        raise ValidationError("Duration must be greater than zero.")

    fare = calculate_fare(
        category=category,
        distance_km=distance_km,
        duration_minutes=duration_minutes,
    )

    booking = Booking.objects.create(
        customer=customer,
        category=category,
        pickup_address=pickup_address,
        pickup_latitude=pickup_latitude,
        pickup_longitude=pickup_longitude,
        destination_address=destination_address,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        estimated_distance_km=distance_km,
        estimated_duration_minutes=duration_minutes,
        estimated_fare=fare,
        status=Booking.Status.REQUESTED,
    )

    return booking


def find_eligible_drivers(category: VehicleCategory):
    """
    Find drivers who are currently eligible to receive
    a booking request for the requested vehicle category.
    """

    return DriverProfile.objects.filter(
        user__is_driver=True,
        user__account_status=User.AccountStatus.ACTIVE,
        verification_status=DriverProfile.VerificationStatus.APPROVED,
        availability_status=DriverProfile.AvailabilityStatus.ONLINE,
        vehicles__category=category,
        vehicles__is_active=True,
        vehicles__verification_status="APPROVED",
    ).distinct()

def assign_driver(booking: Booking) -> Booking:
    """
    Assign an eligible driver and matching vehicle to a booking.
    """

    if booking.status != Booking.Status.REQUESTED:
        raise ValidationError(
            "Only requested bookings can be assigned."
        )

    with transaction.atomic():

        eligible_drivers = find_eligible_drivers(
            booking.category
        )

        for driver in eligible_drivers:

            # Lock the driver while assigning the booking.
            driver = (
                DriverProfile.objects
                .select_for_update()
                .get(pk=driver.pk)
            )

            # Check whether the driver already has an active booking.
            driver_is_busy = Booking.objects.filter(
                driver=driver,
                status__in=[
                    Booking.Status.ACCEPTED,
                    Booking.Status.DRIVER_ARRIVING,
                    Booking.Status.DRIVER_ARRIVED,
                    Booking.Status.STARTED,
                ],
            ).exists()

            if driver_is_busy:
                continue

            # Find this driver's active, approved vehicle
            # for the requested category.
            vehicle = (
                Vehicle.objects
                .select_for_update()
                .filter(
                    driver=driver,
                    category=booking.category,
                    is_active=True,
                    verification_status=Vehicle.VerificationStatus.APPROVED,
                )
                .first()
            )

            if vehicle is None:
                continue

            # Assign driver and vehicle.
            booking.driver = driver
            booking.vehicle = vehicle
            booking.status = Booking.Status.ACCEPTED
            booking.accepted_at = timezone.now()
            booking.save(
                update_fields=[
                    "driver",
                    "vehicle",
                    "status",
                    "accepted_at",
                    "updated_at",
                ]
            )

            # Driver is now occupied.
            driver.availability_status = (
                DriverProfile.AvailabilityStatus.BUSY
            )
            driver.save(update_fields=["availability_status"])

            return booking

    raise ValidationError(
        "No eligible driver is currently available."
    )
def mark_driver_arriving(booking: Booking) -> Booking:
    """
    Mark the assigned driver as arriving.
    """

    if booking.status != Booking.Status.ACCEPTED:
        raise ValidationError(
            "Only accepted bookings can be marked as driver arriving."
        )

    if booking.driver is None or booking.vehicle is None:
        raise ValidationError(
            "Booking must have an assigned driver and vehicle."
        )

    booking.status = Booking.Status.DRIVER_ARRIVING

    booking.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return booking

def mark_driver_arrived(booking: Booking) -> Booking:
    """
    Mark the driver as arrived at the pickup location.
    """

    if booking.status != Booking.Status.DRIVER_ARRIVING:
        raise ValidationError(
            "Driver must be arriving before being marked as arrived."
        )

    booking.status = Booking.Status.DRIVER_ARRIVED

    booking.arrived_at = timezone.now()

    booking.save(
        update_fields=[
            "status",
            "arrived_at",
            "updated_at",
        ]
    )

    return booking
def generate_ride_otp(booking: Booking) -> str:
    """
    Generate a 4-digit OTP for starting a ride.
    """

    if booking.status not in (
        Booking.Status.ACCEPTED,
        Booking.Status.DRIVER_ARRIVING,
        Booking.Status.DRIVER_ARRIVED,
    ):
        raise ValidationError(
            "OTP can only be generated for an accepted booking."
        )

    otp = f"{secrets.randbelow(10000):04d}"

    booking.otp_hash = hashlib.sha256(
        otp.encode()
    ).hexdigest()

    booking.otp_verified = False

    booking.save(
        update_fields=[
            "otp_hash",
            "otp_verified",
            "updated_at",
        ]
    )

    return otp
def verify_ride_otp(booking: Booking, otp: str) -> Booking:
    """
    Verify the ride OTP and start the ride.
    """

    if booking.status != Booking.Status.DRIVER_ARRIVED:
        raise ValidationError(
            "OTP can only be verified after the driver has arrived."
        )

    if not booking.otp_hash:
        raise ValidationError(
            "No OTP has been generated for this booking."
        )

    otp_hash = hashlib.sha256(
        otp.encode()
    ).hexdigest()

    if otp_hash != booking.otp_hash:
        raise ValidationError(
            "Invalid ride OTP."
        )

    booking.otp_verified = True
    booking.status = Booking.Status.STARTED
    booking.started_at = timezone.now()

    booking.save(
        update_fields=[
            "otp_verified",
            "status",
            "started_at",
            "updated_at",
        ]
    )

    return booking
def complete_ride(
    booking: Booking,
    final_fare: Decimal,
) -> Booking:
    """
    Complete a started ride.
    """

    if booking.status != Booking.Status.STARTED:
        raise ValidationError(
            "Only started rides can be completed."
        )

    if final_fare < 0:
        raise ValidationError(
            "Final fare cannot be negative."
        )

    if booking.driver is None:
        raise ValidationError(
            "A booking must have an assigned driver."
        )

    with transaction.atomic():

        booking.final_fare = final_fare
        booking.status = Booking.Status.COMPLETED
        booking.completed_at = timezone.now()

        booking.save(
            update_fields=[
                "final_fare",
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        driver = (
            DriverProfile.objects
            .select_for_update()
            .get(pk=booking.driver.pk)
        )

        driver.completed_rides += 1
        driver.availability_status = (
            DriverProfile.AvailabilityStatus.ONLINE
        )

        driver.save(
            update_fields=[
                "completed_rides",
                "availability_status",
            ]
        )

    return booking

def cancel_booking(
    booking: Booking,
    cancelled_by: str,
    reason: str,
) -> Booking:
    """
    Cancel a booking before the ride starts.
    """

    cancellable_statuses = (
        Booking.Status.REQUESTED,
        Booking.Status.SEARCHING,
        Booking.Status.ACCEPTED,
        Booking.Status.DRIVER_ARRIVING,
        Booking.Status.DRIVER_ARRIVED,
    )

    if booking.status not in cancellable_statuses:
        raise ValidationError(
            "This booking cannot be cancelled."
        )

    if cancelled_by not in Booking.CancelledBy.values:
        raise ValidationError(
            "Invalid cancellation source."
        )

    if not reason.strip():
        raise ValidationError(
            "Cancellation reason is required."
        )

    with transaction.atomic():

        booking.status = Booking.Status.CANCELLED
        booking.cancelled_by = cancelled_by
        booking.cancellation_reason = reason
        booking.cancelled_at = timezone.now()

        booking.save(
            update_fields=[
                "status",
                "cancelled_by",
                "cancellation_reason",
                "cancelled_at",
                "updated_at",
            ]
        )

        # Make the assigned driver available again.
        if booking.driver is not None:
            driver = (
                DriverProfile.objects
                .select_for_update()
                .get(pk=booking.driver.pk)
            )

            driver.availability_status = (
                DriverProfile.AvailabilityStatus.ONLINE
            )

            driver.save(
                update_fields=["availability_status"]
            )

    return booking