from django.contrib import admin

from .models import Car, CarBooking



@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "brand",
        "model",
        "year",
        "license_plate",
        "seats",
        "price_per_day",
        "image_url",
        "is_available",
    )

    list_filter = (
        "is_available",
        "brand",
    )

    search_fields = (
        "brand",
        "model",
        "license_plate",
    )


@admin.register(CarBooking)
class CarBookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "car",
        "pickup_location",
        "dropoff_location",
        "pickup_date",
        "return_date",
        "total_price",
        "booking_status",
        "created_at",
    )
    list_filter = (
        "booking_status",
        "pickup_date",
        "return_date",
    )
    search_fields = (
        "user__username",
        "user__email",
        "car__brand",
        "car__model",
        "car__license_plate",
        "pickup_location",
        "dropoff_location",
    )
    readonly_fields = ("created_at", "updated_at")

