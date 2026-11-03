from rest_framework import serializers
from .models import Shipment

class ShipmentSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)  # Status can ONLY change via transition endpoints

    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ('tracking_id', 'status', 'created_at', 'updated_at')