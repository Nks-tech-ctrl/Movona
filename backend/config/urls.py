from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path("admin/", admin.site.urls),

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