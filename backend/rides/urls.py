from django.urls import path

from .views import (
    BookingCancelAPIView,
    BookingCreateAPIView,
    BookingDetailAPIView,
    BookingListAPIView,
    CustomerRateRideAPIView,
    FareEstimateAPIView,
)

urlpatterns = [
    path(
        "estimate/",
        FareEstimateAPIView.as_view(),
        name="fare-estimate",
    ),
    path(
        "book/",
        BookingCreateAPIView.as_view(),
        name="booking-create",
    ),
    path(
        "",
        BookingListAPIView.as_view(),
        name="booking-list",
    ),
    path(
        "<int:pk>/",
        BookingDetailAPIView.as_view(),
        name="booking-detail",
    ),
    path(
        "<int:pk>/cancel/",
        BookingCancelAPIView.as_view(),
        name="booking-cancel",
    ),
    path(
        "<int:pk>/rate/",
        CustomerRateRideAPIView.as_view(),
        name="booking-rate",
    ),
]

