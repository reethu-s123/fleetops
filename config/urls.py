from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from fleet.views import VehicleViewSet, DriverProfileViewSet
from shipments.views import (
    ShipmentViewSet, 
    shipment_tracking_page, 
    analytics_dashboard_page, 
    AnalyticsAPIView,
    TriggerSimulationAPIView,
    master_portal_view
)

# Core REST Framework router
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'drivers', DriverProfileViewSet, basename='driver')
router.register(r'shipments', ShipmentViewSet, basename='shipment')

urlpatterns = [
    # 1. Master All-in-One Enterprise Portal (Root Homepage)
    path('', master_portal_view, name='master_portal'),

    # 2. Django Administration (CSS fully restored via Nginx)
    path('admin/', admin.site.urls),

    # 3. Live GPS Simulation Trigger API
    path('api/trigger-simulation/', TriggerSimulationAPIView.as_view(), name='trigger_simulation'),

    # 4. Analytics REST API & Standalone Dashboard
    path('api/analytics/', AnalyticsAPIView.as_view(), name='api_analytics'),
    path('dashboard/', analytics_dashboard_page, name='analytics_dashboard'),

    # 5. Core Model REST APIs (Vehicles, Drivers, Shipments)
    path('api/', include(router.urls)),

    # 6. Standalone Public Customer Tracking Page
    path('track/<uuid:tracking_id>/', shipment_tracking_page, name='public_tracking_page'),

    # 7. JWT Authentication Endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]