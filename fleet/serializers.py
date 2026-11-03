from rest_framework import serializers
from .models import Vehicle, DriverProfile

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class DriverProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = DriverProfile
        fields = ['id', 'email', 'full_name', 'license_number', 'license_expiry_date', 'assigned_vehicle', 'is_available']