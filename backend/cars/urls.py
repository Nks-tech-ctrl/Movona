from django.urls import path

from .views import CarDetailAPIView, CarListAPIView

urlpatterns = [
    path("", CarListAPIView.as_view(), name="car-list"),
    path("<int:pk>/", CarDetailAPIView.as_view(), name="car-detail"),
]
