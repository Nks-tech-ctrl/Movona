from decimal import Decimal

from rest_framework import serializers

from accounts.models import VehicleCategory
from .models import Booking


class FareEstimateSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=50)
    distance_km = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    duration_minutes = serializers.IntegerField(
        min_value=1,
    )

    def validate_category(self, value):
        try:
            category = VehicleCategory.objects.get(
                name=value,
                is_active=True,
            )
        except VehicleCategory.DoesNotExist:
            raise serializers.ValidationError(
                "Vehicle category is not available."
            )

        return category


class BookingCreateSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=50)

    pickup_address = serializers.CharField(max_length=500)
    pickup_latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
    )
    pickup_longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
    )

    destination_address = serializers.CharField(max_length=500)
    destination_latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
    )
    destination_longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
    )

    distance_km = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    duration_minutes = serializers.IntegerField(
        min_value=1,
    )

    def validate_category(self, value):
        try:
            category = VehicleCategory.objects.get(
                name=value,
                is_active=True,
            )
        except VehicleCategory.DoesNotExist:
            raise serializers.ValidationError(
                "Vehicle category is not available."
            )

        return category


class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=500,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )


class BookingResponseSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    customer_name = serializers.CharField(source="customer.user.username", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "category",
            "customer_name",
            "pickup_address",
            "pickup_latitude",
            "pickup_longitude",
            "destination_address",
            "destination_latitude",
            "destination_longitude",
            "estimated_distance_km",
            "estimated_duration_minutes",
            "estimated_fare",
            "final_fare",
            "cancelled_by",
            "cancellation_reason",
            "requested_at",
            "accepted_at",
            "arrived_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "created_at",
        ]
        read_only_fields = fields


class EligibleRideResponseSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "category",
            "pickup_address",
            "pickup_latitude",
            "pickup_longitude",
            "destination_address",
            "destination_latitude",
            "destination_longitude",
            "estimated_distance_km",
            "estimated_duration_minutes",
            "estimated_fare",
            "requested_at",
        ]
        read_only_fields = fields




class RideStartSerializer(serializers.Serializer):
    otp = serializers.CharField(
        max_length=6,
        min_length=4,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
    )
