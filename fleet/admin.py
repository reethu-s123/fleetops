from django.contrib import admin
from .models import Vehicle, DriverProfile

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'model_name', 'fuel_type', 'max_payload_kg', 'status')
    list_filter = ('status', 'fuel_type')
    search_fields = ('plate_number', 'vin', 'model_name')

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'license_expiry_date', 'assigned_vehicle', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('user__email', 'license_number')