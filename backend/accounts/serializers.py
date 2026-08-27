from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import CustomerProfile, DriverProfile, User


class CustomerRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "A user with that phone number already exists."
            )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Password confirmation does not match."}
            )

        # Validate password against Django's configured auth password validators
        validate_password(password)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        # Explicitly enforce secure customer defaults and prevent privilege escalation
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            password=password,
            is_customer=True,
            is_driver=False,
            is_staff=False,
            is_superuser=False,
            account_status=User.AccountStatus.ACTIVE,
            is_verified=False,
        )

        CustomerProfile.objects.create(user=user)

        return user


class CustomerUserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "is_customer",
            "created_at",
        ]
        read_only_fields = fields


class CustomerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    created_at = serializers.DateTimeField(source="user.created_at", read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "profile_photo",
            "average_rating",
            "total_rides",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "phone",
            "profile_photo",
            "average_rating",
            "total_rides",
            "created_at",
        ]


class DriverProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    created_at = serializers.DateTimeField(source="user.created_at", read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "profile_photo",
            "date_of_birth",
            "verification_status",
            "availability_status",
            "average_rating",
            "completed_rides",
            "created_at",
        ]
        read_only_fields = fields
