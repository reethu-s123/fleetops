from django.urls import re_path
from .consumers import ShipmentTrackingConsumer

websocket_urlpatterns = [
    re_path(r'^ws/track/(?P<tracking_id>[0-9a-f-]+)/$', ShipmentTrackingConsumer.as_asgi()),
]