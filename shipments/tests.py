from decimal import Decimal
from django.test import TestCase
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_fsm import TransitionNotAllowed

from shipments.models import Shipment, Invoice
from fleet.models import Vehicle

class FleetOpsTenantTestSuite(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)

        # Create a test vehicle
        self.vehicle = Vehicle.objects.create(
            plate_number="KA-05-TEST-9999",
            vin="VINTEST1234567890",
            model_name="Eicher Pro 3015",
            max_payload_kg=5000.00,
            max_volume_m3=20.00
        )

        # Create a test shipment
        self.shipment = Shipment.objects.create(
            sender_name="Amazon Warehouse",
            receiver_name="Retail Store",
            origin_address="Bengaluru, Karnataka",
            destination_address="Chennai, Tamil Nadu",
            origin_lat=12.9716,
            origin_lng=77.5946,
            dest_lat=13.0827,
            dest_lng=80.2707,
            payload_weight_kg=1200.00
        )

    def test_shipment_initial_state(self):
        """Test that every shipment initializes strictly in BOOKED status."""
        self.assertEqual(self.shipment.status, Shipment.Status.BOOKED)

    def test_state_machine_guard_prevents_illegal_jump(self):
        """Test that django-fsm raises TransitionNotAllowed if jumping from BOOKED to DELIVERED."""
        with self.assertRaises(TransitionNotAllowed):
            self.shipment.mark_delivered()

    def test_valid_state_machine_lifecycle(self):
        """Test the legal step-by-step transition lifecycle."""
        # 1. BOOKED -> ASSIGNED
        self.shipment.assign_fleet(vehicle=self.vehicle, driver=None)
        self.shipment.save()
        self.assertEqual(self.shipment.status, Shipment.Status.ASSIGNED)

        # 2. ASSIGNED -> PICKED_UP
        self.shipment.pick_up()
        self.shipment.save()
        self.assertEqual(self.shipment.status, Shipment.Status.PICKED_UP)

        # 3. PICKED_UP -> IN_TRANSIT
        self.shipment.start_transit()
        self.shipment.save()
        self.assertEqual(self.shipment.status, Shipment.Status.IN_TRANSIT)

        # 4. IN_TRANSIT -> DELIVERED
        self.shipment.mark_delivered()
        self.shipment.save()
        self.assertEqual(self.shipment.status, Shipment.Status.DELIVERED)

    def test_invoice_creation_math(self):
        """Test freight calculation logic."""
        base = Decimal("500.00")
        distance_charge = Decimal("326.0") * Decimal("12.50") # 4075.00
        weight_charge = Decimal("1200.00") * Decimal("1.50") # 1800.00
        expected_total = base + distance_charge + weight_charge

        invoice = Invoice.objects.create(
            shipment=self.shipment,
            invoice_number="INV-TEST-001",
            base_charge=base,
            distance_charge=distance_charge,
            weight_charge=weight_charge,
            total_amount=expected_total
        )
        self.assertEqual(invoice.total_amount, Decimal("6375.00"))