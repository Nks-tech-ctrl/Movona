from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from accounts.models import CustomerProfile

from .serializers import (
    BookingCreateSerializer,
    FareEstimateSerializer,
)

from .services import (
    calculate_fare,
    create_booking,
)


class FareEstimateAPIView(APIView):
    def post(self, request):
        serializer = FareEstimateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = serializer.validated_data["category"]
        distance_km = serializer.validated_data["distance_km"]
        duration_minutes = serializer.validated_data["duration_minutes"]

        fare = calculate_fare(
            category=category,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

        return Response(
            {
                "category": category.name,
                "distance_km": distance_km,
                "duration_minutes": duration_minutes,
                "estimated_fare": fare,
            },
            status=status.HTTP_200_OK,
        )


class BookingCreateAPIView(APIView):
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer = CustomerProfile.objects.get(user__username="testcustomer")

        category = serializer.validated_data["category"]

        booking = create_booking(
            customer=customer,
            category=category,
            pickup_address=serializer.validated_data["pickup_address"],
            pickup_latitude=serializer.validated_data["pickup_latitude"],
            pickup_longitude=serializer.validated_data["pickup_longitude"],
            destination_address=serializer.validated_data["destination_address"],
            destination_latitude=serializer.validated_data["destination_latitude"],
            destination_longitude=serializer.validated_data["destination_longitude"],
            distance_km=serializer.validated_data["distance_km"],
            duration_minutes=serializer.validated_data["duration_minutes"],
        )

        return Response(
            {
                "id": booking.id,
                "status": booking.status,
                "category": booking.category.name,
                "estimated_fare": booking.estimated_fare,
            },
            status=status.HTTP_201_CREATED,
        )
