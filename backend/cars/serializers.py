from datetime import date
from decimal import Decimal

from rest_framework import serializers

from .models import Car, CarBooking


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = "__all__"


class CarBookingCreateSerializer(serializers.Serializer):
    car_id = serializers.IntegerField()
    pickup_location = serializers.CharField(max_length=255, trim_whitespace=True)
    dropoff_location = serializers.CharField(max_length=255, trim_whitespace=True)
    pickup_date = serializers.DateField()
    return_date = serializers.DateField()

    def validate_car_id(self, value):
        try:
            car = Car.objects.get(pk=value)
        except Car.DoesNotExist:
            raise serializers.ValidationError("Selected car does not exist.")

        if not car.is_available:
            raise serializers.ValidationError("This car is currently unavailable for booking.")

        return value

    def validate(self, attrs):
        pickup_date = attrs.get("pickup_date")
        return_date = attrs.get("return_date")
        car_id = attrs.get("car_id")

        if pickup_date < date.today():
            raise serializers.ValidationError({"pickup_date": "Pickup date cannot be in the past."})

        if return_date <= pickup_date:
            raise serializers.ValidationError({"return_date": "Return date must be after pickup date."})

        # Overlapping booking check
        overlap_exists = CarBooking.objects.filter(
            car_id=car_id,
            booking_status__in=[CarBooking.Status.CONFIRMED, CarBooking.Status.PENDING],
            pickup_date__lt=return_date,
            return_date__gt=pickup_date,
        ).exists()

        if overlap_exists:
            raise serializers.ValidationError(
                {"detail": "This car is already booked for the selected date range. Please choose different dates."}
            )

        return attrs


class CarBookingSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = CarBooking
        fields = [
            "id",
            "user",
            "username",
            "car",
            "pickup_location",
            "dropoff_location",
            "pickup_date",
            "return_date",
            "total_price",
            "booking_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields