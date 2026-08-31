from django.db import models


class Car(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()

    license_plate = models.CharField(max_length=20, unique=True)

    color = models.CharField(max_length=50)

    seats = models.PositiveIntegerField()

    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    image_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Direct URL to car image",
    )

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

