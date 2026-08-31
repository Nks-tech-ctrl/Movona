from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


from cars.views import (
    CarBookingCancelAPIView,
    CarBookingDetailAPIView,
    CarBookingListCreateAPIView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/cars/", include("cars.urls")),
    path(
        "api/bookings/",
        CarBookingListCreateAPIView.as_view(),
        name="booking-list-create",
    ),
    path(
        "api/bookings/<int:pk>/",
        CarBookingDetailAPIView.as_view(),
        name="booking-detail",
    ),
    path(
        "api/bookings/<int:pk>/cancel/",
        CarBookingCancelAPIView.as_view(),
        name="booking-cancel",
    ),
    path(
        "api/rides/",
        include("rides.urls"),
    ),
    path(
        "api/",
        include("accounts.urls"),
    ),
    path(
        "api/auth/token/",
        TokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
]

