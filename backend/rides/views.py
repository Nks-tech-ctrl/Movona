from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsDriver
from .models import Booking
from .serializers import (
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingResponseSerializer,
    EligibleRideResponseSerializer,
    FareEstimateSerializer,
)
from .services import (
    accept_booking,
    calculate_fare,
    cancel_booking,
    create_booking,
    find_eligible_bookings_for_driver,
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


class BookingListAPIView(APIView):
    """
    Retrieve all bookings belonging to the authenticated customer.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = getattr(request.user, "customer_profile", None)
        if customer is None or not getattr(request.user, "is_customer", False):
            return Response(
                {"detail": "Only registered customers can access ride bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        bookings = (
            Booking.objects.filter(customer=customer)
            .select_related("category", "customer__user")
            .order_by("-created_at")
        )
        serializer = BookingResponseSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingDetailAPIView(APIView):
    """
    Retrieve specific booking belonging to the authenticated customer.
    Returns 404 if booking does not exist or belongs to another customer.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        customer = getattr(request.user, "customer_profile", None)
        if customer is None or not getattr(request.user, "is_customer", False):
            return Response(
                {"detail": "Only registered customers can access ride bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.select_related("category", "customer__user").get(
                pk=pk, customer=customer
            )
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookingResponseSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingCancelAPIView(APIView):
    """
    Cancel an existing booking belonging to the authenticated customer.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        customer = getattr(request.user, "customer_profile", None)
        if customer is None or not getattr(request.user, "is_customer", False):
            return Response(
                {"detail": "Only registered customers can cancel ride bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.get(pk=pk, customer=customer)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookingCancelSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = serializer.validated_data["reason"]

        try:
            cancelled_booking = cancel_booking(
                booking=booking,
                cancelled_by=Booking.CancelledBy.CUSTOMER,
                reason=reason,
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = BookingResponseSerializer(cancelled_booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class DriverEligibleRidesAPIView(APIView):
    """
    Retrieve all pending bookings matching the authenticated driver's vehicle categories.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        eligible_bookings = find_eligible_bookings_for_driver(driver)
        serializer = EligibleRideResponseSerializer(eligible_bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DriverAcceptRideAPIView(APIView):
    """
    Accept an eligible booking by the authenticated driver.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can accept ride bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            accepted_booking = accept_booking(booking=booking, driver=driver)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = BookingResponseSerializer(accepted_booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
