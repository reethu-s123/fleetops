import os
import joblib
import numpy as np
from datetime import datetime
from celery import shared_task
from django_tenants.utils import schema_context
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Shipment
from .services import RoutingService, WeatherService

MODEL_PATH = "shipments/ml/delay_model.joblib"

@shared_task
def predict_shipment_delay(schema_name: str, shipment_id: int):
    """
    Asynchronous Celery Task:
    1. Fetches destination coordinates & live weather via Open-Meteo.
    2. Runs scikit-learn model inference.
    3. Saves predicted delay metrics to the database.
    4. Pushes live AI alert to the tracking page via WebSockets!
    """
    with schema_context(schema_name):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return f"Shipment {shipment_id} not found."

        # 1. Fetch live driving distance from OSRM
        route = RoutingService.get_route(
            shipment.origin_lat, shipment.origin_lng,
            shipment.dest_lat, shipment.dest_lng
        )
        distance_km = route['distance_km'] if route else 300.0

        # 2. Fetch live weather at destination via Open-Meteo API
        weather = WeatherService.get_current_weather(
            float(shipment.dest_lat or 13.0827),
            float(shipment.dest_lng or 80.2707)
        )

        # 3. Prepare Feature Vector for Random Forest
        # Features: [distance, payload_weight, weather_severity, departure_hour, is_weekend]
        now = datetime.now()
        hour = now.hour
        is_weekend = 1 if now.weekday() >= 5 else 0
        features = np.array([[
            float(distance_km),
            float(shipment.payload_weight_kg),
            int(weather['severity']),
            int(hour),
            int(is_weekend)
        ]])

        # 4. Run Machine Learning Inference
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            # Probability of delay (Class 1)
            delay_prob = float(model.predict_proba(features)[0][1])
        else:
            delay_prob = 0.25

        is_delayed = delay_prob > 0.50

        # 5. Save back to the database
        shipment.predicted_delay_prob = round(delay_prob, 2)
        shipment.is_delayed_predicted = is_delayed
        shipment.weather_condition = weather['condition']
        shipment.weather_temperature = weather['temperature']
        shipment.weather_windspeed = weather['windspeed']
        shipment.save()

        # 6. Push real-time AI alert to open customer tracking page
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"tracking_{shipment.tracking_id}",
            {
                'type': 'ai_alert',
                'prob': round(delay_prob * 100),
                'is_delayed': is_delayed,
                'condition': weather['condition'],
                'temperature': weather['temperature']
            }
        )

        return f"AI Prediction complete: {round(delay_prob * 100)}% risk of delay."
from datetime import date, timedelta
from fleet.models import DriverProfile
from .models import Invoice


@shared_task
def generate_shipment_invoice(schema_name: str, shipment_id: int):
    """
    Triggered when a shipment is marked DELIVERED.
    Computes freight charges and creates the Invoice record.
    """
    with schema_context(schema_name):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return f"Shipment {shipment_id} not found."

        # Avoid duplicate invoices
        if hasattr(shipment, 'invoice'):
            return f"Invoice already exists for shipment {shipment_id}."

        # Pricing formula:
        # Distance charge: ₹ 12.50 per km (approx 326 km = ~₹ 4075)
        # Weight charge: ₹ 1.50 per kg
        route = RoutingService.get_route(shipment.origin_lat, shipment.origin_lng, shipment.dest_lat, shipment.dest_lng)
        distance_km = route['distance_km'] if route else 300.0

        base_charge = 500.00
        distance_charge = round(float(distance_km) * 12.50, 2)
        weight_charge = round(float(shipment.payload_weight_kg) * 1.50, 2)
        total_amount = round(base_charge + distance_charge + weight_charge, 2)

        invoice_number = f"INV-{shipment.created_at.strftime('%Y%m')}-{shipment.id:04d}"

        invoice = Invoice.objects.create(
            shipment=shipment,
            invoice_number=invoice_number,
            base_charge=base_charge,
            distance_charge=distance_charge,
            weight_charge=weight_charge,
            total_amount=total_amount,
            is_paid=False
        )

        return f"Created {invoice_number} with total: INR {total_amount}"


@shared_task
def check_driver_license_expiry():
    """
    Periodic task run daily by Celery Beat:
    Scans all drivers across tenants whose licenses expire within 30 days.
    """
    from customers.models import Client
    tenants = Client.objects.exclude(schema_name='public')
    alert_count = 0

    threshold_date = date.today() + timedelta(days=30)

    for tenant in tenants:
        with schema_context(tenant.schema_name):
            expiring_drivers = DriverProfile.objects.filter(
                license_expiry_date__lte=threshold_date,
                is_available=True
            )
            for driver in expiring_drivers:
                days_left = (driver.license_expiry_date - date.today()).days
                print(f"⚠️ [COMPLIANCE ALERT] Tenant '{tenant.name}': Driver {driver.user.email} license expires in {days_left} days!")
                alert_count += 1

    return f"License expiry scan complete. {alert_count} alerts raised."