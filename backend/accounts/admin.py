from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, CustomerProfile, DriverProfile,VehicleCategory,Vehicle


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Movana Information",
            {
                "fields": (
                    "phone",
                    "is_customer",
                    "is_driver",
                    "account_status",
                    "is_verified",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_display = (
        "username",
        "email",
        "phone",
        "is_customer",
        "is_driver",
        "account_status",
        "is_verified",
        "is_staff",
    )

    list_filter = (
        "is_customer",
        "is_driver",
        "account_status",
        "is_verified",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date_of_birth",
        "average_rating",
        "total_rides",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__phone",
    )


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "verification_status",
        "availability_status",
        "average_rating",
        "completed_rides",
    )

    list_filter = (
        "verification_status",
        "availability_status",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__phone",
    )
@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "passenger_capacity",
        "base_fare",
        "per_km_rate",
        "per_minute_rate",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "driver",
        "category",
        "make",
        "model",
        "verification_status",
        "is_active",
    )

    list_filter = (
        "category",
        "verification_status",
        "is_active",
    )

    search_fields = (
        "registration_number",
        "make",
        "model",
        "driver__user__username",
        "driver__user__email",
        "driver__user__phone",
    )