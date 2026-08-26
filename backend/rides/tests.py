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