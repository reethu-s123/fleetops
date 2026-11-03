import time
from django.core.management.base import BaseCommand
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from shipments.models import Shipment
from shipments.services import RoutingService

class Command(BaseCommand):
    help = 'Simulates a driver moving in real-time along the highway route'

    def add_arguments(self, parser):
        parser.add_argument('--tracking-id', type=str, required=True, help='Shipment UUID')

    def handle(self, *args, **options):
        tracking_id = options['tracking_id']
        try:
            shipment = Shipment.objects.get(tracking_id=tracking_id)
        except Shipment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Shipment {tracking_id} not found"))
            return

        self.stdout.write(self.style.SUCCESS(f"Fetching highway geometry for shipment {tracking_id}..."))

        route_data = RoutingService.get_route(
            shipment.origin_lat, shipment.origin_lng,
            shipment.dest_lat, shipment.dest_lng
        )

        if not route_data or 'geometry' not in route_data:
            self.stdout.write(self.style.ERROR("Could not retrieve route geometry from OSRM"))
            return

        coords = route_data['geometry']['coordinates']
        self.stdout.write(self.style.SUCCESS(f"Route loaded with {len(coords)} GPS checkpoints."))
        self.stdout.write(self.style.WARNING("Starting live simulation! Watch your browser map..."))

        channel_layer = get_channel_layer()
        group_name = f"tracking_{tracking_id}"

        # Downsample coordinates so the trip animates smoothly across ~30 steps
        step = max(1, len(coords) // 35)
        path = coords[::step]
        if coords[-1] not in path:
            path.append(coords[-1])

        for index, point in enumerate(path):
            lng, lat = point[0], point[1]

            # Broadcast live GPS position via Redis & WebSockets
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'location_update',
                    'lat': lat,
                    'lng': lng,
                    'bearing': 0
                }
            )

            progress = round(((index + 1) / len(path)) * 100)
            self.stdout.write(f"🚚 Ping {index + 1}/{len(path)} -> Lat: {lat:.4f}, Lng: {lng:.4f} [{progress}%]")
            time.sleep(1)  # 1 second delay between GPS pings

        self.stdout.write(self.style.SUCCESS("🎉 Simulation complete! Driver has reached destination."))