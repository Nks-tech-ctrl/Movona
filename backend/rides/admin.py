from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "driver",
        "vehicle",
        "category",
        "status",
        "estimated_fare",
        "final_fare",
        "requested_at",
    )

    list_filter = (
        "status",
        "category",
        "cancelled_by",
        "otp_verified",
    )

    search_fields = (
        "customer__user__username",
        "customer__user__email",
        "customer__user__phone",
        "driver__user__username",
        "driver__user__email",
        "driver__user__phone",
        "vehicle__registration_number",
    )

    readonly_fields = (
        "requested_at",
        "accepted_at",
        "arrived_at",
        "started_at",
        "completed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Booking",
            {
                "fields": (
                    "customer",
                    "driver",
                    "vehicle",
                    "category",
                    "status",
                )
            },
        ),
        (
            "Pickup",
            {
                "fields": (
                    "pickup_address",
                    "pickup_latitude",
                    "pickup_longitude",
                )
            },
        ),
        (
            "Destination",
            {
                "fields": (
                    "destination_address",
                    "destination_latitude",
                    "destination_longitude",
                )
            },
        ),
        (
            "Trip & Fare",
            {
                "fields": (
                    "estimated_distance_km",
                    "estimated_duration_minutes",
                    "estimated_fare",
                    "final_fare",
                )
            },
        ),
        (
            "Ride Verification",
            {
                "fields": (
                    "otp_hash",
                    "otp_verified",
                )
            },
        ),
        (
            "Cancellation",
            {
                "fields": (
                    "cancelled_by",
                    "cancellation_reason",
                    "cancelled_at",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "requested_at",
                    "accepted_at",
                    "arrived_at",
                    "started_at",
                    "completed_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )