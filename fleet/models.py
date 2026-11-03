from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active / On Duty'
        MAINTENANCE = 'MAINTENANCE', 'In Maintenance'
        DECOMMISSIONED = 'DECOMMISSIONED', 'Decommissioned'

    class FuelType(models.TextChoices):
        DIESEL = 'DIESEL', 'Diesel'
        PETROL = 'PETROL', 'Petrol'
        ELECTRIC = 'ELECTRIC', 'Electric'
        HYBRID = 'HYBRID', 'Hybrid'

    plate_number = models.CharField(max_length=20, unique=True)
    vin = models.CharField(max_length=50, unique=True, verbose_name="VIN")
    model_name = models.CharField(max_length=100)
    max_payload_kg = models.DecimalField(max_digits=8, decimal_places=2)
    max_volume_m3 = models.DecimalField(max_digits=6, decimal_places=2)
    fuel_type = models.CharField(max_length=20, choices=FuelType.choices, default=FuelType.DIESEL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plate_number} - {self.model_name} ({self.status})"


class DriverProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    assigned_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drivers'
    )
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry_date = models.DateField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Driver: {self.user.get_full_name() or self.user.email} (Lic: {self.license_number})"