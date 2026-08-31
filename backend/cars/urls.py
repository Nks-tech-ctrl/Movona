from django.urls import path

from .views import (
    CarBookingCancelAPIView,
    CarBookingDetailAPIView,
    CarBookingListCreateAPIView,
    CarDetailAPIView,
    CarListAPIView,
)

urlpatterns = [
    path("", CarListAPIView.as_view(), name="car-list"),
    path("<int:pk>/", CarDetailAPIView.as_view(), name="car-detail"),
    path(
        "bookings/",
        CarBookingListCreateAPIView.as_view(),
        name="car-booking-list-create",
    ),
    path(
        "bookings/<int:pk>/",
        CarBookingDetailAPIView.as_view(),
        name="car-booking-detail",
    ),
    path(
        "bookings/<int:pk>/cancel/",
        CarBookingCancelAPIView.as_view(),
        name="car-booking-cancel",
    ),
]

