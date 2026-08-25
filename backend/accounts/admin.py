from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, CustomerProfile, DriverProfile


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