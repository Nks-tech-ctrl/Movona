from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


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
