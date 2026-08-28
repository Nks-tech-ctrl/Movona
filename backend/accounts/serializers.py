from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import (
    CustomerProfile,
    DriverProfile,
    User,
    Vehicle,
    VehicleCategory,
)


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


class VehicleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleCategory
        fields = [
            "id",
            "name",
            "description",
            "passenger_capacity",
            "base_fare",
            "per_km_rate",
            "per_minute_rate",
            "is_active",
        ]
        read_only_fields = fields


class DriverVehicleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "category",
            "category_name",
            "make",
            "model",
            "registration_number",
            "colour",
            "seating_capacity",
            "verification_status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_name",
            "verification_status",
            "created_at",
            "updated_at",
        ]


class DriverVehicleCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=VehicleCategory.objects.filter(is_active=True)
    )

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "category",
            "make",
            "model",
            "registration_number",
            "colour",
            "seating_capacity",
            "verification_status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "verification_status",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_registration_number(self, value):
        reg = value.strip().upper()
        if Vehicle.objects.filter(registration_number__iexact=reg).exists():
            raise serializers.ValidationError(
                "A vehicle with this registration number already exists."
            )
        return reg

    def create(self, validated_data):
        driver = self.context["driver"]
        validated_data["verification_status"] = Vehicle.VerificationStatus.PENDING
        validated_data["is_active"] = False
        return Vehicle.objects.create(driver=driver, **validated_data)


class DriverVehicleUpdateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=VehicleCategory.objects.filter(is_active=True),
        required=False,
    )

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "category",
            "make",
            "model",
            "registration_number",
            "colour",
            "seating_capacity",
            "verification_status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "verification_status",
            "created_at",
            "updated_at",
        ]

    def validate_registration_number(self, value):
        reg = value.strip().upper()
        if (
            Vehicle.objects.filter(registration_number__iexact=reg)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "A vehicle with this registration number already exists."
            )
        return reg

    def validate(self, attrs):
        is_active = attrs.get("is_active")
        if is_active is True:
            if self.instance.verification_status != Vehicle.VerificationStatus.APPROVED:
                raise serializers.ValidationError(
                    {"is_active": "Only approved vehicles can be activated."}
                )
        return attrs


class DriverProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            "date_of_birth",
            "availability_status",
        ]

    def validate_availability_status(self, value):
        if value == DriverProfile.AvailabilityStatus.BUSY:
            raise serializers.ValidationError("Cannot manually set status to BUSY.")

        if value == DriverProfile.AvailabilityStatus.ONLINE:
            if (
                self.instance.verification_status
                != DriverProfile.VerificationStatus.APPROVED
            ):
                raise serializers.ValidationError(
                    "Unapproved drivers cannot go online."
                )

        if value == DriverProfile.AvailabilityStatus.OFFLINE:
            if (
                self.instance.availability_status
                == DriverProfile.AvailabilityStatus.BUSY
            ):
                raise serializers.ValidationError(
                    "Cannot go offline while on an active ride."
                )

        return value
