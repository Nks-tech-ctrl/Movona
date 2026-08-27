from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    BookingCreateSerializer,
    BookingResponseSerializer,
    FareEstimateSerializer,
)
from .services import (
    calculate_fare,
    create_booking,
)


class FareEstimateAPIView(APIView):
    permission_classes = [AllowAny]

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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Resolve CustomerProfile strictly from authenticated request.user
        customer = getattr(request.user, "customer_profile", None)
        if customer is None or not getattr(request.user, "is_customer", False):
            return Response(
                {"detail": "Only registered customers can create ride bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2. Validate booking payload
        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = serializer.validated_data["category"]

        # 3. Create booking using service layer
        try:
            booking = create_booking(
                customer=customer,
                category=category,
                pickup_address=serializer.validated_data["pickup_address"],
                pickup_latitude=serializer.validated_data["pickup_latitude"],
                pickup_longitude=serializer.validated_data["pickup_longitude"],
                destination_address=serializer.validated_data["destination_address"],
                destination_latitude=serializer.validated_data["destination_latitude"],
                destination_longitude=serializer.validated_data[
                    "destination_longitude"
                ],
                distance_km=serializer.validated_data["distance_km"],
                duration_minutes=serializer.validated_data["duration_minutes"],
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Return safe serialized response
        response_serializer = BookingResponseSerializer(booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
