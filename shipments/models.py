import uuid
from django.db import models
from django.conf import settings
from django_fsm import FSMField, transition
from fleet.models import Vehicle, DriverProfile

class Shipment(models.Model):
    class Status(models.TextChoices):
        BOOKED = 'BOOKED', 'Booked'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        PICKED_UP = 'PICKED_UP', 'Picked Up'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sender_name = models.CharField(max_length=100)
    receiver_name = models.CharField(max_length=100)
    origin_address = models.CharField(max_length=255)
    destination_address = models.CharField(max_length=255)
    
    # Geographic coordinates (for Leaflet mapping and OSRM routing in Week 3)
    origin_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    origin_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dest_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dest_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    payload_weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    payload_volume_m3 = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    assigned_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    # Ensure protected is set to False:
    status = FSMField(default=Status.BOOKED, choices=Status.choices, protected=False)

    # State Machine field
    status = FSMField(default=Status.BOOKED, choices=Status.choices, protected=True)
    
    # AI/ML Prediction Fields
    predicted_delay_prob = models.FloatField(default=0.0, help_text="AI Delay probability from 0.0 to 1.0")
    is_delayed_predicted = models.BooleanField(default=False)
    weather_condition = models.CharField(max_length=100, blank=True, default="Unknown")
    weather_temperature = models.FloatField(null=True, blank=True)
    weather_windspeed = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment {str(self.tracking_id)[:8]} - {self.status}"

    # FSM State Transitions
    @transition(field=status, source=Status.BOOKED, target=Status.ASSIGNED)
    def assign_fleet(self, vehicle, driver):
        self.assigned_vehicle = vehicle
        self.assigned_driver = driver

    @transition(field=status, source=Status.ASSIGNED, target=Status.PICKED_UP)
    def pick_up(self):
        """Triggered when driver confirms package pickup"""
        pass

    @transition(field=status, source=Status.PICKED_UP, target=Status.IN_TRANSIT)
    def start_transit(self):
        """Triggered when driver starts moving towards destination"""
        pass

    @transition(field=status, source=Status.IN_TRANSIT, target=Status.DELIVERED)
    def mark_delivered(self):
        """Triggered on delivery confirmation"""
        pass

    @transition(field=status, source=[Status.BOOKED, Status.ASSIGNED], target=Status.CANCELLED)
    def cancel_shipment(self):
        """Only allowed before the shipment is picked up"""
        pass

class Invoice(models.Model):
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    base_charge = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    distance_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weight_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - Total: ₹{self.total_amount}"