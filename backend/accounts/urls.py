from django.urls import path

from .views import (
    CustomerProfileAPIView,
    CustomerRegisterAPIView,
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
]
