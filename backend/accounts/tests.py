from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from accounts.models import User
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
