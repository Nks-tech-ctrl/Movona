from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from accounts.models import CustomerProfile, DriverProfile, User
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
