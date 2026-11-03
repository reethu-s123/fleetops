from django.contrib import admin
from .models import Shipment

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_id', 
        'sender_name', 
        'receiver_name', 
        'payload_weight_kg', 
        'status', 
        'assigned_driver', 
        'assigned_vehicle'
    )
    list_filter = ('status',)
    search_fields = ('tracking_id', 'sender_name', 'receiver_name')
    readonly_fields = ('tracking_id', 'status', 'created_at', 'updated_at')

    # Custom Admin actions to trigger FSM transitions safely
    actions = ['mark_as_picked_up', 'mark_as_in_transit', 'mark_as_delivered']

    @admin.action(description='Transition: Picked Up')
    def mark_as_picked_up(self, request, queryset):
        for shipment in queryset:
            try:
                shipment.pick_up()
                shipment.save()
            except Exception as e:
                self.message_user(request, f"Error on {shipment}: {str(e)}", level='error')

    @admin.action(description='Transition: In Transit')
    def mark_as_in_transit(self, request, queryset):
        for shipment in queryset:
            try:
                shipment.start_transit()
                shipment.save()
            except Exception as e:
                self.message_user(request, f"Error on {shipment}: {str(e)}", level='error')

    @admin.action(description='Transition: Delivered')
    def mark_as_delivered(self, request, queryset):
        for shipment in queryset:
            try:
                shipment.mark_delivered()
                shipment.save()
            except Exception as e:
                self.message_user(request, f"Error on {shipment}: {str(e)}", level='error')