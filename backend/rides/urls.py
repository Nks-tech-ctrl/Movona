from django.urls import path

from .views import (
    BookingCreateAPIView,
    FareEstimateAPIView
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
]