from decimal import Decimal

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Car, CarBooking
from .serializers import (
    CarBookingCreateSerializer,
    CarBookingSerializer,
    CarSerializer,
)


class CarListAPIView(generics.ListAPIView):
    queryset = Car.objects.all()
    serializer_class = CarSerializer


class CarDetailAPIView(generics.RetrieveAPIView):
    queryset = Car.objects.all()
    serializer_class = CarSerializer


class CarBookingListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = (
            CarBooking.objects.filter(user=request.user)
            .select_related("car", "user")
            .order_by("-created_at")
        )
        serializer = CarBookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CarBookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        car = Car.objects.get(pk=validated_data["car_id"])

        pickup_date = validated_data["pickup_date"]
        return_date = validated_data["return_date"]
        rental_days = max((return_date - pickup_date).days, 1)
        total_price = Decimal(rental_days) * car.price_per_day

        booking = CarBooking.objects.create(
            user=request.user,
            car=car,
            pickup_location=validated_data["pickup_location"],
            dropoff_location=validated_data["dropoff_location"],
            pickup_date=pickup_date,
            return_date=return_date,
            total_price=total_price,
            booking_status=CarBooking.Status.CONFIRMED,
        )

        response_serializer = CarBookingSerializer(booking)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CarBookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            booking = CarBooking.objects.select_related("car", "user").get(
                pk=pk, user=request.user
            )
        except CarBooking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CarBookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CarBookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = CarBooking.objects.get(pk=pk, user=request.user)
        except CarBooking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if booking.booking_status in [
            CarBooking.Status.COMPLETED,
            CarBooking.Status.CANCELLED,
        ]:
            return Response(
                {
                    "detail": f"Cannot cancel booking with status '{booking.booking_status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.booking_status = CarBooking.Status.CANCELLED
        booking.save(update_fields=["booking_status", "updated_at"])

        serializer = CarBookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
