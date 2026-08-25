from django.core.management.base import BaseCommand
from accounts.models import VehicleCategory


class Command(BaseCommand):
    help = "Create default Movana vehicle categories"

    categories = [
        {
            "name": "Mini",
            "description": "Affordable rides for everyday local travel.",
            "passenger_capacity": 4,
        },
        {
            "name": "Sedan",
            "description": "Comfortable standard rides.",
            "passenger_capacity": 4,
        },
        {
            "name": "SUV",
            "description": "Spacious rides for groups and luggage.",
            "passenger_capacity": 6,
        },
        {
            "name": "Premium",
            "description": "Premium and higher-comfort rides.",
            "passenger_capacity": 4,
        },
    ]

    def handle(self, *args, **options):
        for category_data in self.categories:
            category, created = VehicleCategory.objects.get_or_create(
                name=category_data["name"],
                defaults={
                    "description": category_data["description"],
                    "passenger_capacity": category_data["passenger_capacity"],
                    "base_fare": 0,
                    "per_km_rate": 0,
                    "per_minute_rate": 0,
                    "is_active": True,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created category: {category.name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Already exists: {category.name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("Vehicle category seeding completed.")
        )