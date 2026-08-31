from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Car


class CarAPITests(APITestCase):
    def setUp(self):
        self.car1 = Car.objects.create(
            brand="Toyota",
            model="Fortuner",
            year=2024,
            license_plate="DL01AB1111",
            color="White",
            seats=7,
            price_per_day=Decimal("4999.99"),
            is_available=True,
        )
        self.car2 = Car.objects.create(
            brand="Honda",
            model="City",
            year=2023,
            license_plate="DL01CD2222",
            color="Black",
            seats=5,
            price_per_day=Decimal("2500.00"),
            is_available=False,
        )

    def test_get_car_list_returns_200_and_all_cars(self):
        response = self.client.get("/api/cars/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_car_detail_valid_id_returns_200(self):
        response = self.client.get(f"/api/cars/{self.car1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.car1.id)
        self.assertEqual(response.data["brand"], "Toyota")
        self.assertEqual(response.data["model"], "Fortuner")
        self.assertEqual(response.data["year"], 2024)
        self.assertEqual(response.data["seats"], 7)
        self.assertEqual(Decimal(response.data["price_per_day"]), Decimal("4999.99"))
        self.assertTrue(response.data["is_available"])

    def test_get_car_detail_invalid_id_returns_404(self):
        response = self.client.get("/api/cars/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
