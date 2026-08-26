from rest_framework import serializers

from accounts.models import VehicleCategory


class FareEstimateSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=50)
    distance_km = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )
    duration_minutes = serializers.IntegerField(
        min_value=0,
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