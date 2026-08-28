from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Vehicle, VehicleCategory
from .permissions import IsDriver
from .serializers import (
    CustomerProfileSerializer,
    CustomerRegisterSerializer,
    CustomerUserResponseSerializer,
    DriverProfileSerializer,
    DriverProfileUpdateSerializer,
    DriverVehicleCreateSerializer,
    DriverVehicleSerializer,
    DriverVehicleUpdateSerializer,
    VehicleCategorySerializer,
)


class CustomerRegisterAPIView(APIView):
    """
    Public registration endpoint for new customers.
    Creates a User and associated CustomerProfile.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        response_serializer = CustomerUserResponseSerializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CustomerProfileAPIView(APIView):
    """
    Authenticated endpoint to retrieve and update the current customer's profile.
    Uses request.user.customer_profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "customer_profile", None)
        if profile is None:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = getattr(request.user, "customer_profile", None)
        if profile is None:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DriverProfileAPIView(APIView):
    """
    Authenticated endpoint to retrieve and update the current driver's profile.
    Uses request.user.driver_profile.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        profile = getattr(request.user, "driver_profile", None)
        if profile is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DriverProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = getattr(request.user, "driver_profile", None)
        if profile is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DriverProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_profile = serializer.save()
        response_serializer = DriverProfileSerializer(updated_profile)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class VehicleCategoryListAPIView(APIView):
    """
    Public endpoint to list all available vehicle categories.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        categories = VehicleCategory.objects.filter(is_active=True).order_by(
            "base_fare"
        )
        serializer = VehicleCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DriverVehicleListCreateAPIView(APIView):
    """
    List vehicles belonging to the authenticated driver or register a new vehicle.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        vehicles = (
            Vehicle.objects.filter(driver=driver)
            .select_related("category")
            .order_by("-created_at")
        )
        serializer = DriverVehicleSerializer(vehicles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DriverVehicleCreateSerializer(
            data=request.data,
            context={"driver": driver},
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        vehicle = serializer.save()
        response_serializer = DriverVehicleSerializer(vehicle)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class DriverVehicleDetailAPIView(APIView):
    """
    Retrieve, update, or remove a vehicle belonging to the authenticated driver.
    """

    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            vehicle = Vehicle.objects.select_related("category").get(
                pk=pk, driver=driver
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DriverVehicleSerializer(vehicle)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            vehicle = Vehicle.objects.get(pk=pk, driver=driver)
        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DriverVehicleUpdateSerializer(
            vehicle,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_vehicle = serializer.save()
        response_serializer = DriverVehicleSerializer(updated_vehicle)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        driver = getattr(request.user, "driver_profile", None)
        if driver is None:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            vehicle = Vehicle.objects.get(pk=pk, driver=driver)
        except Vehicle.DoesNotExist:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if vehicle is in an active ride
        from rides.models import Booking

        active_statuses = [
            Booking.Status.ACCEPTED,
            Booking.Status.DRIVER_ARRIVING,
            Booking.Status.DRIVER_ARRIVED,
            Booking.Status.STARTED,
        ]
        if Booking.objects.filter(vehicle=vehicle, status__in=active_statuses).exists():
            return Response(
                {"detail": "Cannot delete vehicle with active bookings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vehicle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
