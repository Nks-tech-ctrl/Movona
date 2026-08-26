from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .serializers import FareEstimateSerializer
from .services import calculate_fare


class FareEstimateAPIView(APIView):

    def post(self, request):
        serializer = FareEstimateSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = serializer.validated_data["category"]
        distance_km = serializer.validated_data["distance_km"]
        duration_minutes = serializer.validated_data[
            "duration_minutes"
        ]

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