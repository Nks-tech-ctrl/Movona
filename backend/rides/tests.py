from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import (
    CustomerProfile,
    DriverProfile,
    User,
    Vehicle,
    VehicleCategory,
)

from .models import Booking
from .services import (
    assign_driver,
    calculate_fare,
    cancel_booking,
    complete_ride,
    create_booking,
    find_eligible_drivers,
    generate_ride_otp,
    mark_driver_arrived,
    mark_driver_arriving,
    verify_ride_otp,
)
from rest_framework import status
from rest_framework.test import APITestCase


class BookingServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testcustomer",
            email="customer@test.com",
            phone="9999999998",
            is_customer=True,
        )

        self.customer = CustomerProfile.objects.create(
            user=self.user
        )

        self.category = VehicleCategory.objects.create(
            name="Test Mini",
            description="Test category",
            passenger_capacity=4,
            base_fare=Decimal("50.00"),
            per_km_rate=Decimal("10.00"),
            per_minute_rate=Decimal("2.00"),
            is_active=True,
        )

    def test_calculate_fare(self):
        fare = calculate_fare(
            category=self.category,
            distance_km=Decimal("8.00"),
            duration_minutes=20,
        )

        self.assertEqual(
            fare,
            Decimal("170.00"),
        )

    def test_create_booking(self):
        booking = create_booking(
            customer=self.customer,
            category=self.category,
            pickup_address="Test Pickup",
            pickup_latitude=Decimal("28.6315"),
            pickup_longitude=Decimal("77.2167"),
            destination_address="Test Destination",
            destination_latitude=Decimal("28.6129"),
            destination_longitude=Decimal("77.2295"),
            distance_km=Decimal("8.00"),
            duration_minutes=20,
        )

        self.assertEqual(
            booking.status,
            Booking.Status.REQUESTED,
        )

        self.assertEqual(
            booking.estimated_fare,
            Decimal("170.00"),
        )

        self.assertEqual(
            booking.customer,
            self.customer,
        )

        self.assertEqual(
            booking.category,
            self.category,
        )

    def test_zero_distance_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_booking(
                customer=self.customer,
                category=self.category,
                pickup_address="Test Pickup",
                pickup_latitude=Decimal("28.6315"),
                pickup_longitude=Decimal("77.2167"),
                destination_address="Test Destination",
                destination_latitude=Decimal("28.6129"),
                destination_longitude=Decimal("77.2295"),
                distance_km=Decimal("0"),
                duration_minutes=20,
            )

    def test_zero_duration_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_booking(
                customer=self.customer,
                category=self.category,
                pickup_address="Test Pickup",
                pickup_latitude=Decimal("28.6315"),
                pickup_longitude=Decimal("77.2167"),
                destination_address="Test Destination",
                destination_latitude=Decimal("28.6129"),
                destination_longitude=Decimal("77.2295"),
                distance_km=Decimal("8.00"),
                duration_minutes=0,
            )

    def test_inactive_category_is_rejected(self):
        self.category.is_active = False
        self.category.save()

        with self.assertRaises(ValidationError):
            create_booking(
                customer=self.customer,
                category=self.category,
                pickup_address="Test Pickup",
                pickup_latitude=Decimal("28.6315"),
                pickup_longitude=Decimal("77.2167"),
                destination_address="Test Destination",
                destination_latitude=Decimal("28.6129"),
                destination_longitude=Decimal("77.2295"),
                distance_km=Decimal("8.00"),
                duration_minutes=20,
            )


class RideTestBase(TestCase):

    def setUp(self):
        # Customer
        customer_user = User.objects.create_user(
            username="testcustomer",
            email="customer@test.com",
            phone="9999999997",
            is_customer=True,
        )

        self.customer = CustomerProfile.objects.create(
            user=customer_user
        )

        # Vehicle category
        self.category = VehicleCategory.objects.create(
            name="Test Sedan",
            description="Test category",
            passenger_capacity=4,
            base_fare=Decimal("50.00"),
            per_km_rate=Decimal("10.00"),
            per_minute_rate=Decimal("2.00"),
            is_active=True,
        )

        # Driver user
        driver_user = User.objects.create_user(
            username="testdriver",
            email="driver@test.com",
            phone="8888888887",
            is_driver=True,
            is_customer=False,
            is_verified=True,
            account_status=User.AccountStatus.ACTIVE,
        )

        # Driver profile
        self.driver = DriverProfile.objects.create(
            user=driver_user,
            verification_status=(
                DriverProfile.VerificationStatus.APPROVED
            ),
            availability_status=(
                DriverProfile.AvailabilityStatus.ONLINE
            ),
        )

        # Driver vehicle
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            category=self.category,
            make="Maruti",
            model="Swift",
            registration_number="TEST1234",
            colour="White",
            seating_capacity=4,
            verification_status=(
                Vehicle.VerificationStatus.APPROVED
            ),
            is_active=True,
        )

        # Booking
        self.booking = create_booking(
            customer=self.customer,
            category=self.category,
            pickup_address="Test Pickup",
            pickup_latitude=Decimal("28.6315"),
            pickup_longitude=Decimal("77.2167"),
            destination_address="Test Destination",
            destination_latitude=Decimal("28.6129"),
            destination_longitude=Decimal("77.2295"),
            distance_km=Decimal("8.00"),
            duration_minutes=20,
        )


class DriverAssignmentTests(RideTestBase):

    def test_driver_is_eligible(self):
        eligible_drivers = find_eligible_drivers(
            self.category
        )

        self.assertIn(
            self.driver,
            eligible_drivers,
        )

    def test_driver_assignment(self):
        booking = assign_driver(self.booking)

        self.assertEqual(
            booking.status,
            Booking.Status.ACCEPTED,
        )

        self.assertEqual(
            booking.driver,
            self.driver,
        )

        self.assertEqual(
            booking.vehicle,
            self.vehicle,
        )

    def test_driver_becomes_busy(self):
        assign_driver(self.booking)

        self.driver.refresh_from_db()

        self.assertEqual(
            self.driver.availability_status,
            DriverProfile.AvailabilityStatus.BUSY,
        )


class RideLifecycleTests(RideTestBase):

    def setUp(self):
        super().setUp()

        self.booking = assign_driver(
            self.booking
        )

    def test_driver_arriving(self):
        self.booking = mark_driver_arriving(
            self.booking
        )

        self.assertEqual(
            self.booking.status,
            Booking.Status.DRIVER_ARRIVING,
        )

    def test_driver_arrived(self):
        self.booking = mark_driver_arriving(
            self.booking
        )

        self.booking = mark_driver_arrived(
            self.booking
        )

        self.assertEqual(
            self.booking.status,
            Booking.Status.DRIVER_ARRIVED,
        )

        self.assertIsNotNone(
            self.booking.arrived_at
        )

    def test_invalid_otp_is_rejected(self):
        self.booking = mark_driver_arriving(
            self.booking
        )

        self.booking = mark_driver_arrived(
            self.booking
        )

        generate_ride_otp(
            self.booking
        )

        with self.assertRaises(ValidationError):
            verify_ride_otp(
                self.booking,
                "0000",
            )

        self.booking.refresh_from_db()

        self.assertFalse(
            self.booking.otp_verified
        )

        self.assertEqual(
            self.booking.status,
            Booking.Status.DRIVER_ARRIVED,
        )

    def test_valid_otp_starts_ride(self):
        self.booking = mark_driver_arriving(
            self.booking
        )

        self.booking = mark_driver_arrived(
            self.booking
        )

        otp = generate_ride_otp(
            self.booking
        )

        self.booking = verify_ride_otp(
            self.booking,
            otp,
        )

        self.assertEqual(
            self.booking.status,
            Booking.Status.STARTED,
        )

        self.assertTrue(
            self.booking.otp_verified
        )

        self.assertIsNotNone(
            self.booking.started_at
        )

    def test_complete_ride(self):
        self.booking = mark_driver_arriving(
            self.booking
        )

        self.booking = mark_driver_arrived(
            self.booking
        )

        otp = generate_ride_otp(
            self.booking
        )

        self.booking = verify_ride_otp(
            self.booking,
            otp,
        )

        self.booking = complete_ride(
            self.booking,
            Decimal("180.00"),
        )

        self.assertEqual(
            self.booking.status,
            Booking.Status.COMPLETED,
        )

        self.assertEqual(
            self.booking.final_fare,
            Decimal("180.00"),
        )

        self.assertIsNotNone(
            self.booking.completed_at
        )

        self.driver.refresh_from_db()

        self.assertEqual(
            self.driver.completed_rides,
            1,
        )

        self.assertEqual(
            self.driver.availability_status,
            DriverProfile.AvailabilityStatus.ONLINE,
        )

    def test_cancel_booking(self):
        self.booking = cancel_booking(
            self.booking,
            Booking.CancelledBy.CUSTOMER,
            "Customer changed plans",
        )

        self.assertEqual(
            self.booking.status,
            Booking.Status.CANCELLED,
        )

        self.assertEqual(
            self.booking.cancelled_by,
            Booking.CancelledBy.CUSTOMER,
        )

        self.assertEqual(
            self.booking.cancellation_reason,
            "Customer changed plans",
        )

        self.assertIsNotNone(
            self.booking.cancelled_at
        )

    def test_completed_booking_cannot_be_cancelled(self):
        self.booking = mark_driver_arriving(
            self.booking
        )

        self.booking = mark_driver_arrived(
            self.booking
        )

        otp = generate_ride_otp(
            self.booking
        )

        self.booking = verify_ride_otp(
            self.booking,
            otp,
        )

        self.booking = complete_ride(
            self.booking,
            Decimal("180.00"),
        )

        with self.assertRaises(ValidationError):
            cancel_booking(
                self.booking,
                Booking.CancelledBy.CUSTOMER,
                "Trying to cancel completed ride",
            )
class RideAPITests(APITestCase):

    def setUp(self):
        self.password = "CustomerPass123!"
        self.user = User.objects.create_user(
            username="testcustomer",
            email="api@test.com",
            phone="7777777777",
            password=self.password,
            is_customer=True,
        )
        self.customer = CustomerProfile.objects.create(
            user=self.user
        )

        self.user_b = User.objects.create_user(
            username="customertwo",
            email="api2@test.com",
            phone="7777777778",
            password=self.password,
            is_customer=True,
        )
        self.customer_b = CustomerProfile.objects.create(
            user=self.user_b
        )

        self.category = VehicleCategory.objects.create(
            name="API Mini",
            description="API test category",
            passenger_capacity=4,
            base_fare=Decimal("50.00"),
            per_km_rate=Decimal("10.00"),
            per_minute_rate=Decimal("2.00"),
            is_active=True,
        )

        # Authenticate test customer
        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "testcustomer",
                "password": self.password,
            },
            format="json",
        )
        self.access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.valid_booking_data = {
            "category": "API Mini",
            "pickup_address": "Test Pickup",
            "pickup_latitude": "28.6315000",
            "pickup_longitude": "77.2167000",
            "destination_address": "Test Destination",
            "destination_latitude": "28.6129000",
            "destination_longitude": "77.2295000",
            "distance_km": "8.00",
            "duration_minutes": 20,
        }

    def test_fare_estimate_api(self):
        # Clear auth credentials to verify estimate endpoint is accessible publicly
        self.client.credentials()
        response = self.client.post(
            "/api/rides/estimate/",
            {
                "category": "API Mini",
                "distance_km": "8.00",
                "duration_minutes": 20,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["category"],
            "API Mini",
        )
        self.assertEqual(
            Decimal(str(response.data["estimated_fare"])),
            Decimal("170.00"),
        )

    def test_booking_create_api_authenticated_success(self):
        response = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data["status"],
            Booking.Status.REQUESTED,
        )
        self.assertEqual(
            response.data["category"],
            "API Mini",
        )
        self.assertEqual(
            Decimal(str(response.data["estimated_fare"])),
            Decimal("170.00"),
        )

        created_booking = Booking.objects.get(id=response.data["id"])
        self.assertEqual(created_booking.customer, self.customer)
        self.assertEqual(created_booking.category, self.category)
        self.assertEqual(created_booking.status, Booking.Status.REQUESTED)

    def test_booking_create_unauthenticated_returns_401(self):
        self.client.credentials()  # Remove Bearer token
        response = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_booking_create_non_customer_user_returns_403(self):
        driver_user = User.objects.create_user(
            username="justdriver",
            email="driveronly@test.com",
            phone="8888800001",
            password=self.password,
            is_customer=False,
            is_driver=True,
        )
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "justdriver", "password": self.password},
            format="json",
        )
        driver_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {driver_token}")

        response = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_booking_create_cannot_specify_another_customer(self):
        payload_with_spoofed_customer = self.valid_booking_data.copy()
        payload_with_spoofed_customer["customer"] = self.customer_b.id
        payload_with_spoofed_customer["customer_id"] = self.customer_b.id

        response = self.client.post(
            "/api/rides/book/",
            payload_with_spoofed_customer,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        created_booking = Booking.objects.get(id=response.data["id"])
        self.assertEqual(created_booking.customer, self.customer)
        self.assertNotEqual(created_booking.customer, self.customer_b)

    def test_invalid_category_is_rejected(self):
        invalid_data = self.valid_booking_data.copy()
        invalid_data["category"] = "DoesNotExist"

        response = self.client.post(
            "/api/rides/book/",
            invalid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_inactive_category_is_rejected(self):
        self.category.is_active = False
        self.category.save()

        response = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_distance_is_rejected(self):
        zero_distance_data = self.valid_booking_data.copy()
        zero_distance_data["distance_km"] = "0.00"

        response = self.client.post(
            "/api/rides/book/",
            zero_distance_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        negative_distance_data = self.valid_booking_data.copy()
        negative_distance_data["distance_km"] = "-5.00"

        response = self.client.post(
            "/api/rides/book/",
            negative_distance_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_duration_is_rejected(self):
        zero_duration_data = self.valid_booking_data.copy()
        zero_duration_data["duration_minutes"] = 0

        response = self.client.post(
            "/api/rides/book/",
            zero_duration_data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_booking_create_response_does_not_leak_sensitive_fields(self):
        response = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("otp_verified", response.data)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)

    def test_booking_list_authenticated_returns_only_own_bookings(self):
        # Create 2 bookings for Customer A
        self.client.post("/api/rides/book/", self.valid_booking_data, format="json")
        self.client.post("/api/rides/book/", self.valid_booking_data, format="json")

        # Create 1 booking for Customer B
        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "customertwo", "password": self.password},
            format="json",
        )
        token_b = login_b.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        self.client.post("/api/rides/book/", self.valid_booking_data, format="json")

        # Switch back to Customer A and fetch list
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get("/api/rides/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for booking_item in response.data:
            self.assertEqual(booking_item["customer_name"], "testcustomer")

    def test_booking_list_unauthenticated_returns_401(self):
        self.client.credentials()  # Clear auth credentials
        response = self.client.get("/api/rides/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_booking_list_non_customer_returns_403(self):
        driver_user = User.objects.create_user(
            username="driverlist",
            email="driverlist@test.com",
            phone="8888800002",
            password=self.password,
            is_customer=False,
            is_driver=True,
        )
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "driverlist", "password": self.password},
            format="json",
        )
        driver_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {driver_token}")

        response = self.client.get("/api/rides/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_booking_detail_authenticated_returns_own_booking(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        response = self.client.get(f"/api/rides/{booking_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], booking_id)
        self.assertEqual(response.data["customer_name"], "testcustomer")
        self.assertEqual(response.data["category"], "API Mini")
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("password", response.data)

    def test_booking_detail_customer_a_cannot_access_customer_b_booking_returns_404(self):
        # Create booking as Customer B
        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "customertwo", "password": self.password},
            format="json",
        )
        token_b = login_b.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        create_resp_b = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_b_id = create_resp_b.data["id"]

        # Authenticate as Customer A and attempt to view Customer B's booking
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(f"/api/rides/{booking_b_id}/")

        # Must return 404 to avoid leaking existence of the resource
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_booking_detail_unauthenticated_returns_401(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        self.client.credentials()  # Clear credentials
        response = self.client.get(f"/api/rides/{booking_id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_booking_detail_nonexistent_booking_returns_404(self):
        response = self.client.get("/api/rides/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_booking_detail_non_customer_returns_403(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        driver_user = User.objects.create_user(
            username="driverdetail",
            email="driverdetail@test.com",
            phone="8888800003",
            password=self.password,
            is_customer=False,
            is_driver=True,
        )
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "driverdetail", "password": self.password},
            format="json",
        )
        driver_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {driver_token}")

        response = self.client.get(f"/api/rides/{booking_id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_booking_cancel_authenticated_success(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        response = self.client.post(
            f"/api/rides/{booking_id}/cancel/",
            {"reason": "Changed my travel schedule"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.CANCELLED)
        self.assertEqual(response.data["cancelled_by"], Booking.CancelledBy.CUSTOMER)
        self.assertEqual(
            response.data["cancellation_reason"], "Changed my travel schedule"
        )

        # Verify DB state
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertEqual(booking.cancelled_by, Booking.CancelledBy.CUSTOMER)
        self.assertIsNotNone(booking.cancelled_at)

    def test_booking_cancel_customer_a_cannot_cancel_customer_b_booking_returns_404(self):
        # Create booking as Customer B
        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "customertwo", "password": self.password},
            format="json",
        )
        token_b = login_b.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        create_resp_b = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_b_id = create_resp_b.data["id"]

        # Authenticate as Customer A and attempt to cancel Customer B's booking
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            f"/api/rides/{booking_b_id}/cancel/",
            {"reason": "Malicious attempt to cancel another user's ride"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify Customer B's booking remains REQUESTED
        booking_b = Booking.objects.get(id=booking_b_id)
        self.assertEqual(booking_b.status, Booking.Status.REQUESTED)

    def test_booking_cancel_unauthenticated_returns_401(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        self.client.credentials()  # Clear credentials
        response = self.client.post(
            f"/api/rides/{booking_id}/cancel/",
            {"reason": "Cancel without auth"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_booking_cancel_non_customer_returns_403(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        driver_user = User.objects.create_user(
            username="drivercancel",
            email="drivercancel@test.com",
            phone="8888800004",
            password=self.password,
            is_customer=False,
            is_driver=True,
        )
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "drivercancel", "password": self.password},
            format="json",
        )
        driver_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {driver_token}")

        response = self.client.post(
            f"/api/rides/{booking_id}/cancel/",
            {"reason": "Driver trying customer cancel"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_booking_cancel_missing_reason_rejected(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        # Missing reason
        response = self.client.post(
            f"/api/rides/{booking_id}/cancel/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Blank/whitespace reason
        response_blank = self.client.post(
            f"/api/rides/{booking_id}/cancel/",
            {"reason": "   "},
            format="json",
        )
        self.assertEqual(response_blank.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_cancel_completed_booking_rejected(self):
        booking = create_booking(
            customer=self.customer,
            category=self.category,
            pickup_address="Pickup",
            pickup_latitude=Decimal("28.6315"),
            pickup_longitude=Decimal("77.2167"),
            destination_address="Destination",
            destination_latitude=Decimal("28.6129"),
            destination_longitude=Decimal("77.2295"),
            distance_km=Decimal("8.00"),
            duration_minutes=20,
        )
        booking.status = Booking.Status.COMPLETED
        booking.save()

        response = self.client.post(
            f"/api/rides/{booking.id}/cancel/",
            {"reason": "Try to cancel completed ride"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_cancel_already_cancelled_booking_rejected(self):
        booking = create_booking(
            customer=self.customer,
            category=self.category,
            pickup_address="Pickup",
            pickup_latitude=Decimal("28.6315"),
            pickup_longitude=Decimal("77.2167"),
            destination_address="Destination",
            destination_latitude=Decimal("28.6129"),
            destination_longitude=Decimal("77.2295"),
            distance_km=Decimal("8.00"),
            duration_minutes=20,
        )
        booking.status = Booking.Status.CANCELLED
        booking.save()

        response = self.client.post(
            f"/api/rides/{booking.id}/cancel/",
            {"reason": "Try to cancel again"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_cancel_response_does_not_leak_sensitive_fields(self):
        create_resp = self.client.post(
            "/api/rides/book/",
            self.valid_booking_data,
            format="json",
        )
        booking_id = create_resp.data["id"]

        response = self.client.post(
            f"/api/rides/{booking_id}/cancel/",
            {"reason": "Legitimate cancellation"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)


class DriverRideAPITests(APITestCase):

    def setUp(self):
        self.password = "DriverSecret123!"

        # Create Category 1 (Mini)
        self.category_mini = VehicleCategory.objects.create(
            name="Driver Mini",
            description="Mini test category",
            passenger_capacity=4,
            base_fare=Decimal("50.00"),
            per_km_rate=Decimal("10.00"),
            per_minute_rate=Decimal("2.00"),
            is_active=True,
        )

        # Create Category 2 (Sedan)
        self.category_sedan = VehicleCategory.objects.create(
            name="Driver Sedan",
            description="Sedan test category",
            passenger_capacity=4,
            base_fare=Decimal("80.00"),
            per_km_rate=Decimal("15.00"),
            per_minute_rate=Decimal("3.00"),
            is_active=True,
        )

        # Create Customer
        self.customer_user = User.objects.create_user(
            username="ridecustomer",
            email="ridecustomer@test.com",
            phone="9999900010",
            password=self.password,
            is_customer=True,
            is_driver=False,
        )
        self.customer_profile = CustomerProfile.objects.create(
            user=self.customer_user
        )

        # Create Driver
        self.driver_user = User.objects.create_user(
            username="ridedriver",
            email="ridedriver@test.com",
            phone="9999900020",
            password=self.password,
            is_customer=False,
            is_driver=True,
            account_status=User.AccountStatus.ACTIVE,
        )
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            verification_status=DriverProfile.VerificationStatus.APPROVED,
            availability_status=DriverProfile.AvailabilityStatus.ONLINE,
        )

        # Create Vehicle for Driver (Mini)
        self.driver_vehicle = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category_mini,
            make="Toyota",
            model="Yaris",
            registration_number="DL01DR0001",
            colour="White",
            verification_status=Vehicle.VerificationStatus.APPROVED,
            is_active=True,
        )

        # Create Driver B for cross-driver isolation tests
        self.driver_user_b = User.objects.create_user(
            username="ridedriverb",
            email="ridedriverb@test.com",
            phone="9999900021",
            password=self.password,
            is_customer=False,
            is_driver=True,
            account_status=User.AccountStatus.ACTIVE,
        )
        self.driver_profile_b = DriverProfile.objects.create(
            user=self.driver_user_b,
            verification_status=DriverProfile.VerificationStatus.APPROVED,
            availability_status=DriverProfile.AvailabilityStatus.ONLINE,
        )
        self.driver_vehicle_b = Vehicle.objects.create(
            driver=self.driver_profile_b,
            category=self.category_mini,
            make="Hyundai",
            model="i20",
            registration_number="DL01DR0002",
            colour="Silver",
            verification_status=Vehicle.VerificationStatus.APPROVED,
            is_active=True,
        )

        # Authenticate driver
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "ridedriver", "password": self.password},
            format="json",
        )
        self.driver_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.driver_token}")

    def create_test_booking(self, category=None, customer=None, status_val=Booking.Status.REQUESTED):
        if category is None:
            category = self.category_mini
        if customer is None:
            customer = self.customer_profile

        booking = create_booking(
            customer=customer,
            category=category,
            pickup_address="Pickup 123",
            pickup_latitude=Decimal("28.6315"),
            pickup_longitude=Decimal("77.2167"),
            destination_address="Destination 456",
            destination_latitude=Decimal("28.6129"),
            destination_longitude=Decimal("77.2295"),
            distance_km=Decimal("8.00"),
            duration_minutes=20,
        )
        if status_val != Booking.Status.REQUESTED:
            booking.status = status_val
            booking.save()
        return booking

    def test_driver_eligible_rides_valid_driver_success(self):
        booking = self.create_test_booking(category=self.category_mini)

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], booking.id)
        self.assertEqual(response.data[0]["category"], "Driver Mini")
        self.assertEqual(response.data[0]["status"], Booking.Status.REQUESTED)
        self.assertNotIn("otp_hash", response.data[0])
        self.assertNotIn("password", response.data[0])

    def test_driver_eligible_rides_incompatible_category_excluded(self):
        # Booking in Sedan category (driver only has Mini)
        self.create_test_booking(category=self.category_sedan)

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_driver_eligible_rides_assigned_rides_excluded(self):
        booking = self.create_test_booking(category=self.category_mini)
        booking.status = Booking.Status.ACCEPTED
        booking.driver = self.driver_profile
        booking.save()

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_driver_eligible_rides_cancelled_and_completed_excluded(self):
        self.create_test_booking(category=self.category_mini, status_val=Booking.Status.CANCELLED)
        self.create_test_booking(category=self.category_mini, status_val=Booking.Status.COMPLETED)

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_driver_eligible_rides_busy_driver_receives_empty_list(self):
        self.create_test_booking(category=self.category_mini)
        self.driver_profile.availability_status = DriverProfile.AvailabilityStatus.BUSY
        self.driver_profile.save()

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_driver_eligible_rides_offline_driver_receives_empty_list(self):
        self.create_test_booking(category=self.category_mini)
        self.driver_profile.availability_status = DriverProfile.AvailabilityStatus.OFFLINE
        self.driver_profile.save()

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_driver_eligible_rides_unapproved_driver_receives_empty_list(self):
        self.create_test_booking(category=self.category_mini)
        self.driver_profile.verification_status = DriverProfile.VerificationStatus.PENDING
        self.driver_profile.save()

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_driver_eligible_rides_customer_returns_403(self):
        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "ridecustomer", "password": self.password},
            format="json",
        )
        cust_token = login_cust.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {cust_token}")

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_eligible_rides_unauthenticated_returns_401(self):
        self.client.credentials()

        response = self.client.get("/api/drivers/rides/eligible/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_accept_ride_success(self):
        booking = self.create_test_booking(category=self.category_mini)

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.ACCEPTED)
        self.assertIsNotNone(response.data["accepted_at"])

        # Verify DB state
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACCEPTED)
        self.assertEqual(booking.driver, self.driver_profile)
        self.assertEqual(booking.vehicle, self.driver_vehicle)

        self.driver_profile.refresh_from_db()
        self.assertEqual(
            self.driver_profile.availability_status,
            DriverProfile.AvailabilityStatus.BUSY,
        )

    def test_driver_accept_ride_already_assigned_rejected(self):
        booking = self.create_test_booking(category=self.category_mini)
        booking.status = Booking.Status.ACCEPTED
        booking.driver = self.driver_profile
        booking.save()

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_accept_ride_cancelled_or_completed_rejected(self):
        cancelled_booking = self.create_test_booking(
            category=self.category_mini, status_val=Booking.Status.CANCELLED
        )
        response_cancel = self.client.post(
            f"/api/drivers/rides/{cancelled_booking.id}/accept/"
        )
        self.assertEqual(response_cancel.status_code, status.HTTP_400_BAD_REQUEST)

        completed_booking = self.create_test_booking(
            category=self.category_mini, status_val=Booking.Status.COMPLETED
        )
        response_completed = self.client.post(
            f"/api/drivers/rides/{completed_booking.id}/accept/"
        )
        self.assertEqual(response_completed.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_accept_ride_incompatible_category_rejected(self):
        sedan_booking = self.create_test_booking(category=self.category_sedan)

        response = self.client.post(f"/api/drivers/rides/{sedan_booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_accept_ride_busy_driver_rejected(self):
        booking = self.create_test_booking(category=self.category_mini)
        self.driver_profile.availability_status = DriverProfile.AvailabilityStatus.BUSY
        self.driver_profile.save()

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_accept_ride_offline_driver_rejected(self):
        booking = self.create_test_booking(category=self.category_mini)
        self.driver_profile.availability_status = DriverProfile.AvailabilityStatus.OFFLINE
        self.driver_profile.save()

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_accept_ride_unapproved_driver_rejected(self):
        booking = self.create_test_booking(category=self.category_mini)
        self.driver_profile.verification_status = DriverProfile.VerificationStatus.PENDING
        self.driver_profile.save()

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_accept_ride_nonexistent_booking_returns_404(self):
        response = self.client.post("/api/drivers/rides/999999/accept/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_driver_accept_ride_customer_returns_403(self):
        booking = self.create_test_booking(category=self.category_mini)

        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "ridecustomer", "password": self.password},
            format="json",
        )
        cust_token = login_cust.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {cust_token}")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_accept_ride_unauthenticated_returns_401(self):
        booking = self.create_test_booking(category=self.category_mini)
        self.client.credentials()

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_accept_ride_response_does_not_leak_sensitive_fields(self):
        booking = self.create_test_booking(category=self.category_mini)

        response = self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)

    # -------------------------------------------------------------
    # DRIVER ARRIVING TESTS
    # -------------------------------------------------------------

    def test_driver_arriving_success(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.DRIVER_ARRIVING)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.DRIVER_ARRIVING)

    def test_driver_arriving_unauthenticated_returns_401(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        self.client.credentials()
        response = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_arriving_customer_returns_403(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "ridecustomer", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_cust.data['access']}")
        response = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_arriving_another_driver_returns_404(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        # Login as Driver B
        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "ridedriverb", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_b.data['access']}")
        response = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_driver_arriving_invalid_state_rejected(self):
        booking = self.create_test_booking()  # In REQUESTED state

        response = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        # Not yet assigned/accepted
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Accept booking, then test after cancelled
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        booking.refresh_from_db()
        booking.status = Booking.Status.CANCELLED
        booking.save()

        response_cancelled = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.assertEqual(response_cancelled.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_arriving_response_does_not_leak_sensitive_fields(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)

    # -------------------------------------------------------------
    # DRIVER ARRIVED TESTS
    # -------------------------------------------------------------

    def test_driver_arrived_success(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.DRIVER_ARRIVED)
        self.assertIsNotNone(response.data["arrived_at"])

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.DRIVER_ARRIVED)
        self.assertIsNotNone(booking.arrived_at)
        self.assertTrue(bool(booking.otp_hash))

    def test_driver_arrived_unauthenticated_returns_401(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        self.client.credentials()
        response = self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_arrived_customer_returns_403(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "ridecustomer", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_cust.data['access']}")
        response = self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_arrived_another_driver_returns_404(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")

        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "ridedriverb", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_b.data['access']}")
        response = self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_driver_arrived_invalid_state_rejected(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        # Booking is ACCEPTED, not DRIVER_ARRIVING

        response = self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------
    # OTP VERIFICATION / RIDE START TESTS
    # -------------------------------------------------------------

    def test_driver_start_ride_valid_otp_success(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)  # Get the plaintext OTP

        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.STARTED)
        self.assertIsNotNone(response.data["started_at"])

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.STARTED)
        self.assertTrue(booking.otp_verified)
        self.assertIsNotNone(booking.started_at)

    def test_driver_start_ride_invalid_otp_rejected(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": "0000"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.DRIVER_ARRIVED)
        self.assertFalse(booking.otp_verified)

    def test_driver_start_ride_missing_or_blank_otp_rejected(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        # Missing
        response_missing = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {},
            format="json",
        )
        self.assertEqual(response_missing.status_code, status.HTTP_400_BAD_REQUEST)

        # Blank
        response_blank = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": "   "},
            format="json",
        )
        self.assertEqual(response_blank.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_start_ride_another_driver_returns_404(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)

        # Switch to Driver B
        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "ridedriverb", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_b.data['access']}")

        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_driver_start_ride_customer_returns_403(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)

        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "ridecustomer", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_cust.data['access']}")

        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_start_ride_unauthenticated_returns_401(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        self.client.credentials()
        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": "1234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_start_ride_not_arrived_state_rejected(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        # Booking is in ACCEPTED state

        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": "1234"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_start_ride_response_does_not_leak_sensitive_fields(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)

        response = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("otp_verified", response.data)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)

    def test_driver_start_ride_cannot_replay(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)

        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        # Attempt to call start again
        response_replay = self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        self.assertEqual(response_replay.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------
    # COMPLETE RIDE TESTS
    # -------------------------------------------------------------

    def test_driver_complete_ride_success(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)
        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        response = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Booking.Status.COMPLETED)
        self.assertIsNotNone(response.data["completed_at"])
        self.assertEqual(
            Decimal(str(response.data["final_fare"])),
            booking.estimated_fare,
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)
        self.assertIsNotNone(booking.completed_at)

        self.driver_profile.refresh_from_db()
        self.assertEqual(
            self.driver_profile.availability_status,
            DriverProfile.AvailabilityStatus.ONLINE,
        )
        self.assertEqual(self.driver_profile.completed_rides, 1)

    def test_driver_complete_ride_before_started_rejected(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_complete_ride_another_driver_returns_404(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)
        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        # Switch to Driver B
        login_b = self.client.post(
            "/api/auth/token/",
            {"username": "ridedriverb", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_b.data['access']}")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_driver_complete_ride_customer_returns_403(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)
        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "ridecustomer", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_cust.data['access']}")

        response = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_complete_ride_unauthenticated_returns_401(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)
        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        self.client.credentials()
        response = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_driver_complete_ride_completed_cannot_transition_again(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)
        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )
        self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        # Attempt to complete again
        response_again = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")
        self.assertEqual(response_again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_complete_ride_response_does_not_leak_sensitive_fields(self):
        booking = self.create_test_booking()
        self.client.post(f"/api/drivers/rides/{booking.id}/accept/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arriving/")
        self.client.post(f"/api/drivers/rides/{booking.id}/arrived/")

        booking.refresh_from_db()
        otp = generate_ride_otp(booking)
        self.client.post(
            f"/api/drivers/rides/{booking.id}/start/",
            {"otp": otp},
            format="json",
        )

        response = self.client.post(f"/api/drivers/rides/{booking.id}/complete/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("otp_hash", response.data)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)
