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
    RideStartSerializer,
)
from .services import (
    accept_booking,
    calculate_fare,
    cancel_booking,
    complete_ride,
    create_booking,
    find_eligible_bookings_for_driver,
    mark_driver_arrived,
    mark_driver_arriving,
    verify_ride_otp,
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
    Supports optional status filtering: ?status=COMPLETED
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = getattr(request.user, "customer_profile", None)
        if customer is None or not getattr(request.user, "is_customer", False):
            return Response(
                {"detail": "Only registered customers can access ride bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        status_filter = request.query_params.get("status")
        queryset = Booking.objects.filter(customer=customer)

        if status_filter:
            status_upper = status_filter.strip().upper()
            if status_upper not in Booking.Status.values:
                return Response(
                    {
                        "detail": f"Invalid status filter. Valid choices are: {', '.join(Booking.Status.values)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_upper)

        bookings = (
            queryset.select_related("category", "customer__user")
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


class DriverRideListAPIView(APIView):
    """
    Retrieve all bookings assigned to the authenticated driver.
    Supports optional status filtering: ?status=COMPLETED
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can access driver ride history."},
                status=status.HTTP_403_FORBIDDEN,
            )

        status_filter = request.query_params.get("status")
        queryset = Booking.objects.filter(driver=driver)

        if status_filter:
            status_upper = status_filter.strip().upper()
            if status_upper not in Booking.Status.values:
                return Response(
                    {
                        "detail": f"Invalid status filter. Valid choices are: {', '.join(Booking.Status.values)}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_upper)

        bookings = (
            queryset.select_related("category", "customer__user")
            .order_by("-created_at")
        )
        serializer = BookingResponseSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DriverRideDetailAPIView(APIView):
    """
    Retrieve specific booking assigned to the authenticated driver.
    Returns 404 if booking does not exist or belongs to another driver.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can access driver ride details."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.select_related("category", "customer__user").get(
                pk=pk, driver=driver
            )
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookingResponseSerializer(booking)
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


class DriverArrivingAPIView(APIView):
    """
    Mark an accepted booking as DRIVER_ARRIVING.
    Only the assigned driver can update this ride.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can update ride status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.get(pk=pk, driver=driver)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            updated_booking = mark_driver_arriving(booking)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = BookingResponseSerializer(updated_booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class DriverArrivedAPIView(APIView):
    """
    Mark a booking as DRIVER_ARRIVED when the driver arrives at pickup.
    Only the assigned driver can update this ride.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can update ride status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.get(pk=pk, driver=driver)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            updated_booking = mark_driver_arrived(booking)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = BookingResponseSerializer(updated_booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class DriverStartRideAPIView(APIView):
    """
    Verify customer OTP and transition booking to STARTED.
    Only the assigned driver can start the ride.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can start a ride."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.get(pk=pk, driver=driver)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RideStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = serializer.validated_data["otp"]

        try:
            started_booking = verify_ride_otp(booking, otp)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = BookingResponseSerializer(started_booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class DriverCompleteRideAPIView(APIView):
    """
    Complete a started ride, finalize fare, and free driver availability.
    Only the assigned driver can complete the ride.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None or not getattr(request.user, "is_driver", False):
            return Response(
                {"detail": "Only registered drivers can complete a ride."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            booking = Booking.objects.get(pk=pk, driver=driver)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            completed_booking = complete_ride(booking)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.message if hasattr(exc, "message") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = BookingResponseSerializer(completed_booking)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
