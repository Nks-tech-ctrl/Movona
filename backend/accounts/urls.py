from django.urls import path

from rides.views import (
    DriverAcceptRideAPIView,
    DriverEligibleRidesAPIView,
)
from .views import (
    CustomerProfileAPIView,
    CustomerRegisterAPIView,
    DriverProfileAPIView,
)

urlpatterns = [
    path(
        "auth/register/",
        CustomerRegisterAPIView.as_view(),
        name="customer-register",
    ),
    path(
        "customers/me/",
        CustomerProfileAPIView.as_view(),
        name="customer-profile-me",
    ),
    path(
        "drivers/me/",
        DriverProfileAPIView.as_view(),
        name="driver-profile-me",
    ),
    path(
        "drivers/rides/eligible/",
        DriverEligibleRidesAPIView.as_view(),
        name="driver-rides-eligible",
    ),
    path(
        "drivers/rides/<int:pk>/accept/",
        DriverAcceptRideAPIView.as_view(),
        name="driver-ride-accept",
    ),
]
