from django.db.models import Sum, Count, Q, Avg
from django.core.cache import cache
from django.db import connection

from .models import Shipment, Invoice
from fleet.models import Vehicle

class AnalyticsService:
    @classmethod
    def get_dashboard_metrics(cls, use_cache: bool = True):
        """
        Gathers high-level tenant logistics metrics directly via PostgreSQL ORM aggregations.
        Caches results in Redis with a 10-minute TTL.
        """
        schema_name = connection.schema_name
        cache_key = f"analytics_dashboard_{schema_name}"

        # 1. Try returning cached data from Redis
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data['from_cache'] = True
                return cached_data

        # 2. Compute metrics in PostgreSQL
        total_shipments = Shipment.objects.count()

        status_counts = Shipment.objects.aggregate(
            booked=Count('id', filter=Q(status=Shipment.Status.BOOKED)),
            assigned=Count('id', filter=Q(status=Shipment.Status.ASSIGNED)),
            in_transit=Count('id', filter=Q(status=Shipment.Status.IN_TRANSIT)),
            delivered=Count('id', filter=Q(status=Shipment.Status.DELIVERED)),
            cancelled=Count('id', filter=Q(status=Shipment.Status.CANCELLED)),
        )

        # Revenue Aggregation from Invoices
        revenue_data = Invoice.objects.aggregate(
            total_revenue=Sum('total_amount'),
            paid_revenue=Sum('total_amount', filter=Q(is_paid=True)),
            unpaid_revenue=Sum('total_amount', filter=Q(is_paid=False))
        )

        total_revenue = float(revenue_data['total_revenue'] or 0.0)
        paid_revenue = float(revenue_data['paid_revenue'] or 0.0)

        # Fleet Utilization
        total_vehicles = Vehicle.objects.count()
        active_vehicles = Vehicle.objects.filter(status=Vehicle.Status.ACTIVE).count()
        fleet_utilization = round((active_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0.0

        # AI Delay Prediction Statistics
        delayed_predicted_count = Shipment.objects.filter(is_delayed_predicted=True).count()
        avg_delay_risk = Shipment.objects.aggregate(avg_risk=Avg('predicted_delay_prob'))['avg_risk'] or 0.0
        on_time_rate = round(100 - (avg_delay_risk * 100), 1) if total_shipments > 0 else 100.0

        metrics = {
            'total_shipments': total_shipments,
            'status_distribution': {
                'Booked': status_counts['booked'],
                'Assigned': status_counts['assigned'],
                'In Transit': status_counts['in_transit'],
                'Delivered': status_counts['delivered'],
                'Cancelled': status_counts['cancelled'],
            },
            'financials': {
                'total_revenue': total_revenue,
                'paid_revenue': paid_revenue,
                'outstanding_revenue': total_revenue - paid_revenue
            },
            'fleet': {
                'total_vehicles': total_vehicles,
                'active_vehicles': active_vehicles,
                'utilization_rate': fleet_utilization
            },
            'ai_insights': {
                'on_time_rate': on_time_rate,
                'flagged_delays': delayed_predicted_count,
                'avg_delay_probability': round(avg_delay_risk * 100, 1)
            },
            'from_cache': False
        }

        # 3. Store in Redis cache for 600 seconds (10 minutes)
        cache.set(cache_key, metrics, timeout=600)

        return metrics