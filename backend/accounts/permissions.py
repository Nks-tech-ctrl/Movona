from rest_framework.permissions import BasePermission


class IsDriver(BasePermission):
    """
    Allows access only to authenticated users who are registered drivers
    and have an associated DriverProfile.
    """

    message = "Only registered drivers can access this endpoint."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_driver", False)
            and getattr(request.user, "driver_profile", None) is not None
        )
