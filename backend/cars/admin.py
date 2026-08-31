from django.contrib import admin
from .models import Car


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