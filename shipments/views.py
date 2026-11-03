import time
import math
import threading
from django.shortcuts import render, get_object_or_404
from django.db import connection
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_fsm import TransitionNotAllowed
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_tenants.utils import schema_context

from .models import Shipment, Invoice
from fleet.models import Vehicle, DriverProfile
from .serializers import ShipmentSerializer
from .services import RoutingService
from .tasks import predict_shipment_delay, generate_shipment_invoice
from .invoice_service import InvoicePDFGenerator
from .analytics import AnalyticsService


class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer

    def get_permissions(self):
        if self.action in ['track_public', 'download_invoice']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='track')
    def track_public(self, request):
        tracking_id = request.query_params.get('tracking_id')
        if not tracking_id:
            return Response({'error': 'tracking_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shipment = Shipment.objects.get(tracking_id=tracking_id)
            return Response({
                'tracking_id': str(shipment.tracking_id),
                'status': shipment.status,
                'sender': shipment.sender_name,
                'receiver': shipment.receiver_name,
                'origin': shipment.origin_address,
                'destination': shipment.destination_address,
                'origin_coords': [
                    float(shipment.origin_lat) if shipment.origin_lat else None,
                    float(shipment.origin_lng) if shipment.origin_lng else None
                ],
                'dest_coords': [
                    float(shipment.dest_lat) if shipment.dest_lat else None,
                    float(shipment.dest_lng) if shipment.dest_lng else None
                ],
                'ai_delay_prob': shipment.predicted_delay_prob,
                'is_delayed_predicted': shipment.is_delayed_predicted,
                'weather_condition': shipment.weather_condition,
                'weather_temperature': shipment.weather_temperature
            })
        except Shipment.DoesNotExist:
            return Response({'error': 'Invalid tracking number'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='route-info')
    def route_info(self, request, pk=None):
        shipment = self.get_object()
        if not all([shipment.origin_lat, shipment.origin_lng, shipment.dest_lat, shipment.dest_lng]):
            return Response({'error': 'Coordinates not available for this shipment.'}, status=status.HTTP_400_BAD_REQUEST)

        route_data = RoutingService.get_route(
            shipment.origin_lat, shipment.origin_lng,
            shipment.dest_lat, shipment.dest_lng
        )
        if not route_data:
            return Response({'error': 'Could not calculate route.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(route_data)

    @action(detail=True, methods=['get'], url_path='download-invoice')
    def download_invoice(self, request, pk=None):
        shipment = self.get_object()
        schema_name = connection.schema_name

        invoice = Invoice.objects.filter(shipment_id=shipment.id).first()
        if not invoice:
            generate_shipment_invoice(schema_name, shipment.id)
            invoice = Invoice.objects.filter(shipment_id=shipment.id).first()

        if not invoice:
            return Response({'error': 'Could not generate invoice.'}, status=500)

        pdf_buffer = InvoicePDFGenerator.generate_pdf(invoice)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice-{invoice.invoice_number}.pdf"'
        return response

    @action(detail=True, methods=['post'], url_path='predict-delay')
    def predict_delay(self, request, pk=None):
        shipment = self.get_object()
        schema_name = connection.schema_name
        predict_shipment_delay.delay(schema_name, shipment.id)
        return Response({'message': 'AI Delay Prediction task queued in Celery worker.', 'shipment_id': shipment.id})

    @action(detail=True, methods=['post'], url_path='pickup')
    def pickup(self, request, pk=None):
        shipment = self.get_object()
        try:
            shipment.pick_up()
            shipment.save()
            return Response({'status': 'Shipment marked as PICKED_UP', 'current_status': shipment.status})
        except TransitionNotAllowed:
            return Response({'error': f"Cannot pick up shipment while in '{shipment.status}' status."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='start-transit')
    def start_transit(self, request, pk=None):
        shipment = self.get_object()
        try:
            shipment.start_transit()
            shipment.save()
            schema_name = connection.schema_name
            predict_shipment_delay.delay(schema_name, shipment.id)
            return Response({'status': 'Shipment is now IN_TRANSIT', 'current_status': shipment.status})
        except TransitionNotAllowed:
            return Response({'error': f"Cannot start transit while in '{shipment.status}' status."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='deliver')
    def deliver(self, request, pk=None):
        shipment = self.get_object()
        try:
            shipment.mark_delivered()
            shipment.save()
            schema_name = connection.schema_name
            generate_shipment_invoice.delay(schema_name, shipment.id)
            return Response({'status': 'Shipment marked as DELIVERED', 'current_status': shipment.status})
        except TransitionNotAllowed:
            return Response({'error': f"Cannot deliver shipment while in '{shipment.status}' status."}, status=status.HTTP_400_BAD_REQUEST)


def shipment_tracking_page(request, tracking_id):
    shipment = get_object_or_404(Shipment, tracking_id=tracking_id)
    return render(request, 'shipments/track.html', {'shipment': shipment})


class AnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(AnalyticsService.get_dashboard_metrics(use_cache=True))


def analytics_dashboard_page(request):
    return render(request, 'shipments/dashboard.html', {'metrics': AnalyticsService.get_dashboard_metrics(use_cache=False)})


# In-Browser Simulation Trigger API
class TriggerSimulationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        tracking_id = request.data.get('tracking_id')
        schema_name = connection.schema_name

        def calculate_compass_bearing(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlon = lon2 - lon1
            x = math.sin(dlon) * math.cos(lat2)
            y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
            return (math.degrees(math.atan2(x, y)) + 360) % 360 - 90

        def run_sim():
            with schema_context(schema_name):
                try:
                    shipment = Shipment.objects.get(tracking_id=tracking_id) if tracking_id else Shipment.objects.first()
                    route_data = RoutingService.get_route(shipment.origin_lat, shipment.origin_lng, shipment.dest_lat, shipment.dest_lng)
                    if not route_data:
                        return
                    coords = route_data['geometry']['coordinates']
                    step = max(1, len(coords) // 40)
                    path = coords[::step]
                    if coords[-1] not in path:
                        path.append(coords[-1])

                    channel_layer = get_channel_layer()
                    group_name = f"tracking_{shipment.tracking_id}"

                    for i in range(len(path)):
                        lng, lat = path[i][0], path[i][1]
                        bearing = calculate_compass_bearing(lat, lng, path[i+1][1], path[i+1][0]) if i < len(path)-1 else 0
                        async_to_sync(channel_layer.group_send)(
                            group_name,
                            {'type': 'location_update', 'lat': lat, 'lng': lng, 'bearing': bearing}
                        )
                        time.sleep(0.35)
                except Exception as e:
                    print("Simulation error:", e)

        threading.Thread(target=run_sim, daemon=True).start()
        return Response({'status': 'GPS simulation streaming live to WebSockets!'})


# Master All-In-One Enterprise Portal View (Fast & Non-Blocking)
def master_portal_view(request):
    schema_name = connection.schema_name
    metrics = AnalyticsService.get_dashboard_metrics(use_cache=False)

    shipment_id = request.GET.get('shipment_id')
    all_shipments = Shipment.objects.all().order_by('-created_at')

    if shipment_id:
        selected_shipment = Shipment.objects.filter(id=shipment_id).first() or all_shipments.first()
    else:
        selected_shipment = all_shipments.first()

    # Active Invoice lookup
    invoice = Invoice.objects.filter(shipment=selected_shipment).first() if selected_shipment else None

    all_invoices = Invoice.objects.all().select_related('shipment').order_by('-created_at')[:15]
    vehicles = Vehicle.objects.all().order_by('-created_at')
    drivers = DriverProfile.objects.all().select_related('user', 'assigned_vehicle')

    context = {
        'schema_name': schema_name,
        'metrics': metrics,
        'selected_shipment': selected_shipment,
        'all_shipments': all_shipments,
        'invoice': invoice,
        'all_invoices': all_invoices,
        'vehicles': vehicles,
        'drivers': drivers,
    }
    return render(request, 'shipments/portal.html', context)