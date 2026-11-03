import os
import random
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from fleet.models import Vehicle
from shipments.models import Shipment, Invoice

SCHEMA_NAME = 'logistics1'

ROUTES = [
    ("Bengaluru, Karnataka", "Chennai, Tamil Nadu", 12.9716, 77.5946, 13.0827, 80.2707, 326),
    ("Mumbai, Maharashtra", "Pune, Maharashtra", 19.0760, 72.8777, 18.5204, 73.8567, 148),
    ("Delhi NCR", "Jaipur, Rajasthan", 28.6139, 77.2090, 26.9124, 75.7873, 270),
    ("Hyderabad, Telangana", "Bengaluru, Karnataka", 17.3850, 78.4867, 12.9716, 77.5946, 570),
    ("Kolkata, West Bengal", "Bhubaneswar, Odisha", 22.5726, 88.3639, 20.2961, 85.8245, 440),
    ("Ahmedabad, Gujarat", "Surat, Gujarat", 23.0225, 72.5714, 21.1702, 72.8311, 265),
    ("Chandigarh, Punjab", "Shimla, Himachal Pradesh", 30.7333, 76.7794, 31.1048, 77.1734, 115),
    ("Kochi, Kerala", "Coimbatore, Tamil Nadu", 9.9312, 76.2673, 11.0168, 76.9558, 190),
]

STATUSES = ['BOOKED', 'ASSIGNED', 'IN_TRANSIT', 'DELIVERED', 'DELIVERED']

print(f"Connecting to schema '{SCHEMA_NAME}' to insert 20 diverse enterprise shipments...")

with schema_context(SCHEMA_NAME):
    # 1. Create Fleet Vehicles
    vehicles = []
    models_list = [
        ('KA-01-AB-1234', 'Volvo FH16 Semi-Truck'),
        ('MH-04-AZ-9988', 'Tata Prima 5530.S'),
        ('DL-01-EQ-4421', 'Ashok Leyland Ecomet'),
        ('TS-09-UB-7711', 'BharatBenz 2823R'),
        ('WB-02-KL-3355', 'Eicher Pro 6028'),
        ('GJ-05-MN-8844', 'Mahindra Blazo X'),
    ]
    for plate, name in models_list:
        v, _ = Vehicle.objects.get_or_create(
            plate_number=plate,
            defaults={
                'vin': f"VIN_{plate.replace('-', '_')}",
                'model_name': name,
                'max_payload_kg': random.randint(10000, 25000),
                'max_volume_m3': random.randint(30, 60),
                'fuel_type': 'DIESEL',
                'status': 'ACTIVE'
            }
        )
        vehicles.append(v)

    # 2. Create 20 Shipments with varied statuses
    clients = [
        ("Samsung Electronics", "Reliance Digital"),
        ("Amazon India Hub", "Flipkart Fulfillment"),
        ("Tata Motors Spares", "Maruti Service Center"),
        ("IKEA Global Stores", "Urban Ladder Warehouse"),
        ("Apple India Logistics", "Croma Megastore"),
        ("Unilever Consumer Goods", "DMart Supermarket"),
    ]

    created_count = 0
    for i in range(1, 21):
        route = random.choice(ROUTES)
        pair = random.choice(clients)
        status_choice = random.choice(STATUSES)
        weight = random.randint(1200, 18000)
        dist = route[6]

        s, created = Shipment.objects.get_or_create(
            sender_name=f"{pair[0]} #{i}",
            receiver_name=f"{pair[1]} #{i}",
            defaults={
                'origin_address': route[0],
                'destination_address': route[1],
                'origin_lat': route[2],
                'origin_lng': route[3],
                'dest_lat': route[4],
                'dest_lng': route[5],
                'payload_weight_kg': weight,
                'status': status_choice,
                'assigned_vehicle': random.choice(vehicles),
                'predicted_delay_prob': round(random.uniform(0.05, 0.45), 2),
                'is_delayed_predicted': random.choice([True, False, False, False]),
                'weather_condition': random.choice(['Clear Sky', 'Mainly Clear', 'Partly Cloudy']),
                'weather_temperature': round(random.uniform(24.0, 33.5), 1)
            }
        )

        # 3. Create Corresponding Invoices with Guaranteed Unique Number
        if not Invoice.objects.filter(shipment=s).exists():
            base = 500.00
            dist_charge = round(dist * 12.50, 2)
            weight_charge = round(weight * 1.50, 2)
            total = round(base + dist_charge + weight_charge, 2)
            is_paid = random.choice([True, True, False])  # 66% paid, 34% outstanding

            # Unique random alphanumeric code (e.g. INV-202611-A8F9C2)
            unique_code = uuid.uuid4().hex[:6].upper()
            invoice_num = f"INV-202611-{unique_code}"

            Invoice.objects.create(
                shipment=s,
                invoice_number=invoice_num,
                base_charge=base,
                distance_charge=dist_charge,
                weight_charge=weight_charge,
                total_amount=total,
                is_paid=is_paid
            )
            created_count += 1

    print(f"✅ Successfully seeded 20 diverse enterprise shipments and {created_count} unique invoices!")