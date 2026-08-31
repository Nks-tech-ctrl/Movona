from decimal import Decimal

from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from accounts.models import (
    CustomerProfile,
    DriverProfile,
    User,
    Vehicle,
    VehicleCategory,
)

from config.urls import urlpatterns as config_urlpatterns


class MockProtectedAPIView(APIView):
    """
    Test-only protected view used to verify Bearer token authentication
    and request.user population.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "message": "Access granted",
                "username": request.user.username,
                "user_id": request.user.id,
            },
            status=status.HTTP_200_OK,
        )


urlpatterns = list(config_urlpatterns) + [
    path("api/test/protected/", MockProtectedAPIView.as_view(), name="test-protected"),
]


@override_settings(ROOT_URLCONF="accounts.tests")
class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.username = "jwtcustomer"
        self.email = "jwt@movona.test"
        self.phone = "9876543210"
        self.password = "SecurePass123!"

        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            phone=self.phone,
            password=self.password,
            is_customer=True,
        )

    def test_login_success_returns_jwt_tokens(self):
        """
        Valid credentials must return HTTP 200 with access and refresh tokens,
        and must not expose passwords or hashes.
        """
        response = self.client.post(
            "/api/auth/token/",
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Security check: Ensure credentials and hashes are not exposed
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)
        self.assertNotIn(self.user.password, str(response.data))

    def test_login_invalid_password_returns_401(self):
        """
        Invalid password must return HTTP 401 Unauthorized.
        """
        response = self.client.post(
            "/api/auth/token/",
            {
                "username": self.username,
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_nonexistent_user_returns_401(self):
        """
        Nonexistent username must return HTTP 401 Unauthorized.
        """
        response = self.client.post(
            "/api/auth/token/",
            {
                "username": "unknown_user",
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials_returns_400(self):
        """
        Missing fields in request body must return HTTP 400 Bad Request.
        """
        response = self.client.post(
            "/api/auth/token/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("password", response.data)

    def test_token_refresh_success(self):
        """
        A valid refresh token must return a new access token with HTTP 200 OK.
        """
        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_token_refresh_invalid_token_returns_401(self):
        """
        An invalid or tampered refresh token must return HTTP 401 Unauthorized.
        """
        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": "invalid.jwt.token.string"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_valid_bearer_token(self):
        """
        Requests with a valid Bearer token must succeed (HTTP 200)
        and populate request.user.
        """
        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )
        access_token = login_response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get("/api/test/protected/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.username)
        self.assertEqual(response.data["user_id"], self.user.id)

    def test_protected_endpoint_without_token_returns_401(self):
        """
        Unauthenticated requests to protected endpoints must return HTTP 401.
        """
        self.client.credentials()  # Clear credentials
        response = self.client.get("/api/test/protected/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_invalid_bearer_token_returns_401(self):
        """
        Requests with an invalid Bearer token must return HTTP 401.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.value")
        response = self.client.get("/api/test/protected/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ROOT_URLCONF="accounts.tests")
class CustomerRegistrationTests(APITestCase):
    def setUp(self):
        self.valid_data = {
            "username": "newcustomer",
            "email": "newcustomer@movona.test",
            "phone": "9876500001",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
        }

    def test_registration_success(self):
        """
        Valid registration creates User, CustomerProfile, hashes password,
        and returns 201 without exposing password/hash.
        """
        response = self.client.post(
            "/api/auth/register/",
            self.valid_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], self.valid_data["username"])
        self.assertEqual(response.data["email"], self.valid_data["email"])
        self.assertEqual(response.data["phone"], self.valid_data["phone"])
        self.assertTrue(response.data["is_customer"])

        # Security check: passwords/hashes must never leak
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)
        self.assertNotIn(self.valid_data["password"], str(response.data))

        # Check DB records
        user = User.objects.get(username=self.valid_data["username"])
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_driver)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.valid_data["password"]))
        self.assertNotEqual(user.password, self.valid_data["password"])

        # CustomerProfile must be automatically created
        self.assertTrue(hasattr(user, "customer_profile"))
        self.assertEqual(user.customer_profile.total_rides, 0)

    def test_registration_duplicate_username_rejected(self):
        """
        Attempting to register with an existing username must return HTTP 400.
        """
        self.client.post("/api/auth/register/", self.valid_data, format="json")

        duplicate_data = self.valid_data.copy()
        duplicate_data["email"] = "different@movona.test"
        duplicate_data["phone"] = "9876500002"

        response = self.client.post(
            "/api/auth/register/",
            duplicate_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_registration_duplicate_email_rejected(self):
        """
        Attempting to register with an existing email must return HTTP 400.
        """
        self.client.post("/api/auth/register/", self.valid_data, format="json")

        duplicate_data = self.valid_data.copy()
        duplicate_data["username"] = "different_user"
        duplicate_data["phone"] = "9876500002"

        response = self.client.post(
            "/api/auth/register/",
            duplicate_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_duplicate_phone_rejected(self):
        """
        Attempting to register with an existing phone number must return HTTP 400.
        """
        self.client.post("/api/auth/register/", self.valid_data, format="json")

        duplicate_data = self.valid_data.copy()
        duplicate_data["username"] = "different_user"
        duplicate_data["email"] = "different@movona.test"

        response = self.client.post(
            "/api/auth/register/",
            duplicate_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_registration_password_mismatch_rejected(self):
        """
        Mismatch between password and password_confirm must return HTTP 400.
        """
        mismatch_data = self.valid_data.copy()
        mismatch_data["password_confirm"] = "DifferentPassword123!"

        response = self.client.post(
            "/api/auth/register/",
            mismatch_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_registration_weak_password_rejected(self):
        """
        A weak/short password violating Django auth validators must return HTTP 400.
        """
        weak_data = self.valid_data.copy()
        weak_data["password"] = "123"
        weak_data["password_confirm"] = "123"

        response = self.client.post(
            "/api/auth/register/",
            weak_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_privilege_escalation_prevented(self):
        """
        Passing admin/staff/driver flags in registration payload must be ignored,
        preventing privilege escalation.
        """
        escalation_data = self.valid_data.copy()
        escalation_data.update(
            {
                "is_staff": True,
                "is_superuser": True,
                "is_driver": True,
                "account_status": "SUSPENDED",
                "is_verified": True,
            }
        )

        response = self.client.post(
            "/api/auth/register/",
            escalation_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username=self.valid_data["username"])
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_driver)
        self.assertTrue(user.is_customer)
        self.assertEqual(user.account_status, User.AccountStatus.ACTIVE)
        self.assertFalse(user.is_verified)


@override_settings(ROOT_URLCONF="accounts.tests")
class CustomerProfileTests(APITestCase):
    def setUp(self):
        self.password = "SecurePass123!"
        self.user = User.objects.create_user(
            username="profilecustomer",
            email="profile@movona.test",
            phone="9876500009",
            password=self.password,
            is_customer=True,
        )
        self.profile = CustomerProfile.objects.create(
            user=self.user,
            address="100 Innovation Way",
            gender="Other",
            date_of_birth="2000-01-01",
        )

        # Obtain JWT access token for authenticated requests
        login_response = self.client.post(
            "/api/auth/token/",
            {
                "username": "profilecustomer",
                "password": self.password,
            },
            format="json",
        )
        self.access_token = login_response.data["access"]

    def test_get_profile_authenticated_success(self):
        """
        Authenticated customer can retrieve their profile details (HTTP 200).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get("/api/customers/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "profilecustomer")
        self.assertEqual(response.data["email"], "profile@movona.test")
        self.assertEqual(response.data["phone"], "9876500009")
        self.assertEqual(response.data["address"], "100 Innovation Way")
        self.assertEqual(response.data["gender"], "Other")
        self.assertEqual(response.data["date_of_birth"], "2000-01-01")
        self.assertEqual(response.data["total_rides"], 0)

        # Security check: Passwords and hashes must not be exposed
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)
        self.assertNotIn(self.password, str(response.data))

    def test_get_profile_unauthenticated_returns_401(self):
        """
        Unauthenticated GET /api/customers/me/ must return HTTP 401.
        """
        self.client.credentials()  # Clear credentials
        response = self.client.get("/api/customers/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_authenticated_success(self):
        """
        Authenticated customer can update allowed profile fields (HTTP 200).
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        update_data = {
            "address": "200 Technology Ave",
            "gender": "Female",
            "date_of_birth": "1998-04-12",
        }
        response = self.client.patch(
            "/api/customers/me/",
            update_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["address"], "200 Technology Ave")
        self.assertEqual(response.data["gender"], "Female")
        self.assertEqual(response.data["date_of_birth"], "1998-04-12")

        # Verify database update
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.address, "200 Technology Ave")
        self.assertEqual(self.profile.gender, "Female")
        self.assertEqual(str(self.profile.date_of_birth), "1998-04-12")

    def test_patch_profile_unauthenticated_returns_401(self):
        """
        Unauthenticated PATCH /api/customers/me/ must return HTTP 401.
        """
        self.client.credentials()  # Clear credentials
        response = self.client.patch(
            "/api/customers/me/",
            {"address": "Should Not Update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_forbidden_fields_cannot_be_changed(self):
        """
        Attempting to modify read-only or privileged fields must be ignored.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/customers/me/",
            {
                "username": "hacked_username",
                "email": "hacked@movona.test",
                "phone": "0000000000",
                "average_rating": "5.00",
                "total_rides": 999,
                "is_staff": True,
                "is_driver": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify DB attributes were not changed
        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        self.assertEqual(self.user.username, "profilecustomer")
        self.assertEqual(self.user.email, "profile@movona.test")
        self.assertEqual(self.user.phone, "9876500009")
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_driver)
        self.assertEqual(self.profile.total_rides, 0)


@override_settings(ROOT_URLCONF="accounts.tests")
class DriverProfileTests(APITestCase):
    def setUp(self):
        self.password = "DriverPass123!"
        self.driver_user = User.objects.create_user(
            username="profiledriver",
            email="driver@movona.test",
            phone="9876500010",
            password=self.password,
            is_customer=False,
            is_driver=True,
        )
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            verification_status=DriverProfile.VerificationStatus.APPROVED,
            availability_status=DriverProfile.AvailabilityStatus.ONLINE,
        )

        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "profiledriver", "password": self.password},
            format="json",
        )
        self.access_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_get_driver_profile_authenticated_success(self):
        response = self.client.get("/api/drivers/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "profiledriver")
        self.assertEqual(response.data["email"], "driver@movona.test")
        self.assertEqual(response.data["phone"], "9876500010")
        self.assertEqual(
            response.data["verification_status"],
            DriverProfile.VerificationStatus.APPROVED,
        )
        self.assertEqual(
            response.data["availability_status"],
            DriverProfile.AvailabilityStatus.ONLINE,
        )

    def test_get_driver_profile_unauthenticated_returns_401(self):
        self.client.credentials()
        response = self.client.get("/api/drivers/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_driver_profile_customer_returns_403(self):
        cust_user = User.objects.create_user(
            username="customertryingdriver",
            email="cust@movona.test",
            phone="9876500011",
            password=self.password,
            is_customer=True,
            is_driver=False,
        )
        CustomerProfile.objects.create(user=cust_user)
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "customertryingdriver", "password": self.password},
            format="json",
        )
        cust_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {cust_token}")

        response = self.client.get("/api/drivers/me/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_profile_response_does_not_leak_passwords_or_hashes(self):
        response = self.client.get("/api/drivers/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", response.data)
        self.assertNotIn("password_hash", response.data)
        self.assertNotIn("otp_hash", response.data)


class DriverProfileUpdateTests(APITestCase):
    def setUp(self):
        self.password = "DriverPass123!"
        self.driver_user = User.objects.create_user(
            username="updatedriver",
            email="updatedriver@test.com",
            phone="9876500099",
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
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "updatedriver", "password": self.password},
            format="json",
        )
        self.token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_update_availability_status_online_to_offline(self):
        response = self.client.patch(
            "/api/drivers/me/",
            {"availability_status": DriverProfile.AvailabilityStatus.OFFLINE},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["availability_status"],
            DriverProfile.AvailabilityStatus.OFFLINE,
        )
        self.driver_profile.refresh_from_db()
        self.assertEqual(
            self.driver_profile.availability_status,
            DriverProfile.AvailabilityStatus.OFFLINE,
        )

    def test_unapproved_driver_cannot_go_online(self):
        self.driver_profile.verification_status = (
            DriverProfile.VerificationStatus.PENDING
        )
        self.driver_profile.availability_status = (
            DriverProfile.AvailabilityStatus.OFFLINE
        )
        self.driver_profile.save()

        response = self.client.patch(
            "/api/drivers/me/",
            {"availability_status": DriverProfile.AvailabilityStatus.ONLINE},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_busy_driver_cannot_manually_change_status(self):
        self.driver_profile.availability_status = DriverProfile.AvailabilityStatus.BUSY
        self.driver_profile.save()

        response = self.client.patch(
            "/api/drivers/me/",
            {"availability_status": DriverProfile.AvailabilityStatus.OFFLINE},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_cannot_manually_set_busy(self):
        response = self.client.patch(
            "/api/drivers/me/",
            {"availability_status": DriverProfile.AvailabilityStatus.BUSY},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VehicleCategoryAPITests(APITestCase):
    def setUp(self):
        self.cat1 = VehicleCategory.objects.create(
            name="Hatchback",
            description="Budget ride",
            passenger_capacity=4,
            base_fare=Decimal("40.00"),
            per_km_rate=Decimal("10.00"),
            per_minute_rate=Decimal("1.50"),
            is_active=True,
        )
        self.cat2 = VehicleCategory.objects.create(
            name="SUV",
            description="Large vehicle",
            passenger_capacity=6,
            base_fare=Decimal("80.00"),
            per_km_rate=Decimal("18.00"),
            per_minute_rate=Decimal("3.00"),
            is_active=False,
        )

    def test_list_vehicle_categories_public(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active categories returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Hatchback")


class DriverVehicleAPITests(APITestCase):
    def setUp(self):
        self.password = "VehiclePass123!"
        self.driver_user = User.objects.create_user(
            username="vehicledriver",
            email="vehicledriver@test.com",
            phone="9876500055",
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

        # Driver B
        self.driver_user_b = User.objects.create_user(
            username="vehicledriverb",
            email="vehicledriverb@test.com",
            phone="9876500056",
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

        # Customer User
        self.customer_user = User.objects.create_user(
            username="vehiclecust",
            email="vehiclecust@test.com",
            phone="9876500057",
            password=self.password,
            is_customer=True,
            is_driver=False,
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.customer_user)

        self.category = VehicleCategory.objects.create(
            name="Prime Sedan",
            passenger_capacity=4,
            base_fare=Decimal("50.00"),
            per_km_rate=Decimal("12.00"),
            per_minute_rate=Decimal("2.00"),
            is_active=True,
        )

        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "vehicledriver", "password": self.password},
            format="json",
        )
        self.driver_token = login_resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.driver_token}")

    def test_driver_create_vehicle_success(self):
        payload = {
            "category": self.category.id,
            "make": "Honda",
            "model": "Civic",
            "registration_number": "DL01AB1234",
            "colour": "Black",
            "seating_capacity": 4,
        }
        response = self.client.post("/api/drivers/vehicles/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["make"], "Honda")
        self.assertEqual(response.data["registration_number"], "DL01AB1234")
        # Enforce server defaults
        self.assertEqual(
            response.data["verification_status"],
            Vehicle.VerificationStatus.PENDING,
        )
        self.assertFalse(response.data["is_active"])

    def test_driver_create_vehicle_duplicate_registration_rejected(self):
        Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1234",
            colour="White",
        )
        payload = {
            "category": self.category.id,
            "make": "Honda",
            "model": "Civic",
            "registration_number": "DL01AB1234",
            "colour": "Black",
        }
        response = self.client.post("/api/drivers/vehicles/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_list_vehicles_scoped_to_driver(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
        )
        # Driver B vehicle
        Vehicle.objects.create(
            driver=self.driver_profile_b,
            category=self.category,
            make="Hyundai",
            model="Verna",
            registration_number="DL01AB2222",
            colour="Grey",
        )

        response = self.client.get("/api/drivers/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], v1.id)

    def test_driver_get_vehicle_detail_success(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
        )
        response = self.client.get(f"/api/drivers/vehicles/{v1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["registration_number"], "DL01AB1111")

    def test_driver_get_another_driver_vehicle_returns_404(self):
        v_b = Vehicle.objects.create(
            driver=self.driver_profile_b,
            category=self.category,
            make="Hyundai",
            model="Verna",
            registration_number="DL01AB2222",
            colour="Grey",
        )
        response = self.client.get(f"/api/drivers/vehicles/{v_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_driver_update_vehicle_success(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
        )
        response = self.client.patch(
            f"/api/drivers/vehicles/{v1.id}/",
            {"colour": "Metallic Blue"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["colour"], "Metallic Blue")

    def test_driver_cannot_self_approve_verification_status(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
            verification_status=Vehicle.VerificationStatus.PENDING,
        )
        response = self.client.patch(
            f"/api/drivers/vehicles/{v1.id}/",
            {"verification_status": Vehicle.VerificationStatus.APPROVED},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        v1.refresh_from_db()
        # verification_status must remain PENDING
        self.assertEqual(
            v1.verification_status,
            Vehicle.VerificationStatus.PENDING,
        )

    def test_driver_cannot_activate_unapproved_vehicle(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
            verification_status=Vehicle.VerificationStatus.PENDING,
            is_active=False,
        )
        response = self.client.patch(
            f"/api/drivers/vehicles/{v1.id}/",
            {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_driver_can_activate_approved_vehicle(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
            verification_status=Vehicle.VerificationStatus.APPROVED,
            is_active=False,
        )
        response = self.client.patch(
            f"/api/drivers/vehicles/{v1.id}/",
            {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_active"])

    def test_driver_delete_vehicle_success(self):
        v1 = Vehicle.objects.create(
            driver=self.driver_profile,
            category=self.category,
            make="Honda",
            model="City",
            registration_number="DL01AB1111",
            colour="White",
        )
        response = self.client.delete(f"/api/drivers/vehicles/{v1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=v1.id).exists())

    def test_driver_delete_another_driver_vehicle_returns_404(self):
        v_b = Vehicle.objects.create(
            driver=self.driver_profile_b,
            category=self.category,
            make="Hyundai",
            model="Verna",
            registration_number="DL01AB2222",
            colour="Grey",
        )
        response = self.client.delete(f"/api/drivers/vehicles/{v_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Vehicle.objects.filter(id=v_b.id).exists())

    def test_customer_access_vehicle_endpoints_returns_403(self):
        login_cust = self.client.post(
            "/api/auth/token/",
            {"username": "vehiclecust", "password": self.password},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_cust.data['access']}"
        )

        response = self.client.get("/api/drivers/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_vehicle_endpoints_returns_401(self):
        self.client.credentials()
        response = self.client.get("/api/drivers/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CurrentUserAPITests(APITestCase):
    def setUp(self):
        self.password = "SecureMePass123!"

        self.customer_user = User.objects.create_user(
            username="me_customer",
            email="me_customer@test.com",
            phone="9777700001",
            password=self.password,
            is_customer=True,
            is_driver=False,
        )
        CustomerProfile.objects.create(user=self.customer_user)

        self.driver_user = User.objects.create_user(
            username="me_driver",
            email="me_driver@test.com",
            phone="9777700002",
            password=self.password,
            is_customer=False,
            is_driver=True,
        )
        DriverProfile.objects.create(user=self.driver_user)

    def test_get_current_user_as_customer_success(self):
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "me_customer", "password": self.password},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "me_customer")
        self.assertEqual(response.data["email"], "me_customer@test.com")
        self.assertTrue(response.data["is_customer"])
        self.assertFalse(response.data["is_driver"])

    def test_get_current_user_as_driver_success(self):
        login_resp = self.client.post(
            "/api/auth/token/",
            {"username": "me_driver", "password": self.password},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}"
        )

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "me_driver")
        self.assertEqual(response.data["email"], "me_driver@test.com")
        self.assertFalse(response.data["is_customer"])
        self.assertTrue(response.data["is_driver"])

    def test_get_current_user_unauthenticated_returns_401(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
