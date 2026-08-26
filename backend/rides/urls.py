from django.urls import path

from .views import FareEstimateAPIView


urlpatterns = [
    path(
        "estimate/",
        FareEstimateAPIView.as_view(),
        name="fare-estimate",
    ),
]