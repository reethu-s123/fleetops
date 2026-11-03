import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ShipmentTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract tracking_id from URL
        self.tracking_id = str(self.scope['url_route']['kwargs']['tracking_id'])
        self.room_group_name = f"tracking_{self.tracking_id}"

        # Join the tracking room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive GPS ping from driver / simulation
    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data.get('lat')
        lng = data.get('lng')
        bearing = data.get('bearing', 0)

        # Broadcast the new position to everyone tracking this shipment
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'location_update',
                'lat': lat,
                'lng': lng,
                'bearing': bearing,
            }
        )

    # Event handler: Broadcast AI prediction alert to browser
    async def ai_alert(self, event):
        await self.send(text_data=json.dumps({
            'type': 'AI_DELAY_ALERT',
            'prob': event['prob'],
            'is_delayed': event['is_delayed'],
            'condition': event['condition'],
            'temperature': event['temperature']
        }))