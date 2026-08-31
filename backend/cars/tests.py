from datetime import date, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Car, CarBooking



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
            image_url="https://example.com/fortuner.jpg",
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
        self.assertEqual(
            response.data[0]["image_url"], "https://example.com/fortuner.jpg"
        )

    def test_get_car_detail_valid_id_returns_200(self):
        response = self.client.get(f"/api/cars/{self.car1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.car1.id)
        self.assertEqual(response.data["brand"], "Toyota")
        self.assertEqual(response.data["model"], "Fortuner")
        self.assertEqual(response.data["year"], 2024)
        self.assertEqual(response.data["seats"], 7)
        self.assertEqual(response.data["image_url"], "https://example.com/fortuner.jpg")
        self.assertEqual(Decimal(response.data["price_per_day"]), Decimal("4999.99"))
        self.assertTrue(response.data["is_available"])

    def test_get_car_detail_invalid_id_returns_404(self):
        response = self.client.get("/api/cars/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CarBookingAPITests(APITestCase):
    def setUp(self):
        self.password = "BookingPass123!"

        self.user_a = User.objects.create_user(
            username="bookcustomer_a",
            email="book_a@test.com",
            phone="9666600001",
            password=self.password,
            is_customer=True,
        )

        self.user_b = User.objects.create_user(
            username="bookcustomer_b",
            email="book_b@test.com",
            phone="9666600002",
            password=self.password,
            is_customer=True,
        )

        self.car = Car.objects.create(
            brand="Toyota",
            model="Fortuner",
            year=2024,
            license_plate="DL01BK1111",
            color="White",
            seats=7,
            price_per_day=Decimal("5000.00"),
            is_available=True,
        )

        self.unavailable_car = Car.objects.create(
            brand="Honda",
            model="City",
            year=2023,
            license_plate="DL01BK2222",
            color="Black",
            seats=5,
            price_per_day=Decimal("2500.00"),
            is_available=False,
        )

        # Login User A
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "bookcustomer_a", "password": self.password},
            format="json",
        )
        self.token_a = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")

    def test_create_car_booking_authenticated_success(self):
        pickup_date = (date.today() + timedelta(days=2)).isoformat()
        return_date = (date.today() + timedelta(days=5)).isoformat()  # 3 days

        payload = {
            "car_id": self.car.id,
            "pickup_location": "Delhi Airport Terminal 3",
            "dropoff_location": "Cyber Hub Gurgaon",
            "pickup_date": pickup_date,
            "return_date": return_date,
        }

        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["car"]["id"], self.car.id)
        self.assertEqual(response.data["pickup_location"], "Delhi Airport Terminal 3")
        self.assertEqual(response.data["dropoff_location"], "Cyber Hub Gurgaon")
        # 3 days * 5000.00 = 15000.00
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("15000.00"))
        self.assertEqual(response.data["booking_status"], CarBooking.Status.CONFIRMED)

        # Also verify database persistence
        booking = CarBooking.objects.get(pk=response.data["id"])
        self.assertEqual(booking.user, self.user_a)
        self.assertEqual(booking.total_price, Decimal("15000.00"))

    def test_create_car_booking_unauthenticated_returns_401(self):
        self.client.credentials()  # Clear auth
        payload = {
            "car_id": self.car.id,
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "pickup_date": (date.today() + timedelta(days=1)).isoformat(),
            "return_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_car_booking_unavailable_car_rejected(self):
        payload = {
            "car_id": self.unavailable_car.id,
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "pickup_date": (date.today() + timedelta(days=1)).isoformat(),
            "return_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_car_booking_past_date_rejected(self):
        payload = {
            "car_id": self.car.id,
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "pickup_date": (date.today() - timedelta(days=2)).isoformat(),
            "return_date": (date.today() + timedelta(days=2)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_car_booking_invalid_date_range_rejected(self):
        payload = {
            "car_id": self.car.id,
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "pickup_date": (date.today() + timedelta(days=5)).isoformat(),
            "return_date": (date.today() + timedelta(days=3)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_car_booking_overlapping_dates_rejected(self):
        pickup1 = (date.today() + timedelta(days=2)).isoformat()
        return1 = (date.today() + timedelta(days=6)).isoformat()

        # Create first booking (Days 2 to 6)
        CarBooking.objects.create(
            user=self.user_a,
            car=self.car,
            pickup_location="Airport",
            dropoff_location="Hotel",
            pickup_date=date.today() + timedelta(days=2),
            return_date=date.today() + timedelta(days=6),
            total_price=Decimal("20000.00"),
            booking_status=CarBooking.Status.CONFIRMED,
        )

        # Attempt overlapping booking (Days 4 to 8)
        payload = {
            "car_id": self.car.id,
            "pickup_location": "Airport",
            "dropoff_location": "Hotel",
            "pickup_date": (date.today() + timedelta(days=4)).isoformat(),
            "return_date": (date.today() + timedelta(days=8)).isoformat(),
        }
        response = self.client.post("/api/bookings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_my_bookings_only_returns_own_bookings(self):
        # User A booking
        CarBooking.objects.create(
            user=self.user_a,
            car=self.car,
            pickup_location="Loc A",
            dropoff_location="Loc B",
            pickup_date=date.today() + timedelta(days=1),
            return_date=date.today() + timedelta(days=3),
            total_price=Decimal("10000.00"),
        )
        # User B booking
        CarBooking.objects.create(
            user=self.user_b,
            car=self.car,
            pickup_location="Loc X",
            dropoff_location="Loc Y",
            pickup_date=date.today() + timedelta(days=10),
            return_date=date.today() + timedelta(days=12),
            total_price=Decimal("10000.00"),
        )

        response = self.client.get("/api/bookings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pickup_location"], "Loc A")

    def test_get_booking_detail_success(self):
        booking = CarBooking.objects.create(
            user=self.user_a,
            car=self.car,
            pickup_location="Loc A",
            dropoff_location="Loc B",
            pickup_date=date.today() + timedelta(days=1),
            return_date=date.today() + timedelta(days=3),
            total_price=Decimal("10000.00"),
        )

        response = self.client.get(f"/api/bookings/{booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], booking.id)
        self.assertEqual(response.data["pickup_location"], "Loc A")

    def test_get_booking_detail_other_user_returns_404(self):
        booking_b = CarBooking.objects.create(
            user=self.user_b,
            car=self.car,
            pickup_location="Loc X",
            dropoff_location="Loc Y",
            pickup_date=date.today() + timedelta(days=1),
            return_date=date.today() + timedelta(days=3),
            total_price=Decimal("10000.00"),
        )

        # Authenticated as User A, querying User B's booking
        response = self.client.get(f"/api/bookings/{booking_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_booking_success(self):
        booking = CarBooking.objects.create(
            user=self.user_a,
            car=self.car,
            pickup_location="Loc A",
            dropoff_location="Loc B",
            pickup_date=date.today() + timedelta(days=1),
            return_date=date.today() + timedelta(days=3),
            total_price=Decimal("10000.00"),
            booking_status=CarBooking.Status.CONFIRMED,
        )

        response = self.client.post(f"/api/bookings/{booking.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["booking_status"], CarBooking.Status.CANCELLED)

        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, CarBooking.Status.CANCELLED)

    def test_cancel_booking_other_user_returns_404(self):
        booking_b = CarBooking.objects.create(
            user=self.user_b,
            car=self.car,
            pickup_location="Loc X",
            dropoff_location="Loc Y",
            pickup_date=date.today() + timedelta(days=1),
            return_date=date.today() + timedelta(days=3),
            total_price=Decimal("10000.00"),
            booking_status=CarBooking.Status.CONFIRMED,
        )

        response = self.client.post(f"/api/bookings/{booking_b.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

