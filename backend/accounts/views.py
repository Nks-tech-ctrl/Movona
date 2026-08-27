from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsDriver
from .serializers import (
    CustomerProfileSerializer,
    CustomerRegisterSerializer,
    CustomerUserResponseSerializer,
    DriverProfileSerializer,
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
    Authenticated endpoint to retrieve the current driver's profile.
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
