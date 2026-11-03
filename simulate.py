import os
import time
import math
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_tenants.utils import schema_context
from shipments.models import Shipment
from shipments.services import RoutingService

TRACKING_ID = "695d2340-23db-431a-90f9-679775842c60"
SCHEMA_NAME = "logistics1"

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculates compass heading angle (0-360) so front face always leads."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    initial_bearing = math.atan2(x, y)
    compass_bearing = (math.degrees(initial_bearing) + 360) % 360
    # Our SVG truck's front faces East (90 deg) by default, so offset is (compass - 90)
    return compass_bearing - 90

with schema_context(SCHEMA_NAME):
    shipment = Shipment.objects.get(tracking_id=TRACKING_ID)
    route_data = RoutingService.get_route(
        shipment.origin_lat, shipment.origin_lng,
        shipment.dest_lat, shipment.dest_lng
    )

    coords = route_data['geometry']['coordinates']

    # Step closely along the highway road bends
    step = max(1, len(coords) // 60)
    path = coords[::step]
    if coords[-1] not in path:
        path.append(coords[-1])

    channel_layer = get_channel_layer()
    group_name = f"tracking_{TRACKING_ID}"

    print(f"\n🚚 Starting route from {shipment.origin_address} to Chennai...")
    print(f"🛣️  Driving along highway path with {len(path)} waypoints.\n")

    for i in range(len(path)):
        lng, lat = path[i][0], path[i][1]

        # Calculate exact angle pointing forward to next point
        if i < len(path) - 1:
            next_lng, next_lat = path[i + 1][0], path[i + 1][1]
            bearing = calculate_bearing(lat, lng, next_lat, next_lng)
        else:
            bearing = 0

        # Broadcast live GPS position
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'location_update',
                'lat': lat,
                'lng': lng,
                'bearing': bearing
            }
        )

        progress = round(((i + 1) / len(path)) * 100)
        print(f"📍 GPS [{i + 1}/{len(path)}] -> Lat: {lat:.4f}, Lng: {lng:.4f} ({progress}%)")
        time.sleep(0.4)  # Fast, smooth animation

    print("\n🎉 The truck has arrived face-forward at Chennai Logistics Port!")