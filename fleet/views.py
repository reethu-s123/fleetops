from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Vehicle, DriverProfile
from .serializers import VehicleSerializer, DriverProfileSerializer
from accounts.permissions import IsDispatcher

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsDispatcher]

class DriverProfileViewSet(viewsets.ModelViewSet):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated, IsDispatcher]