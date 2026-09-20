from django.contrib import admin
from .models import Room, Booking, HotelSettings

# Admin Site Custom Branding
admin.site.site_header = "MAXDEL HOTEL Administration"
admin.site.site_title = "MAXDEL HOTEL Portal"
admin.site.index_title = "Hotel Management System"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'price_per_night', 'status')
    list_filter = ('room_type', 'status')
    search_fields = ('room_number',)
    ordering = ('room_number',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'guest_phone', 'room', 'check_in', 'check_out', 'payment_status', 'checked_out')
    list_filter = ('payment_status', 'checked_out', 'check_in')
    search_fields = ('guest_name', 'guest_phone', 'room__room_number', 'payment_reference')
    ordering = ('-created_at',)


@admin.register(HotelSettings)
class HotelSettingsAdmin(admin.ModelAdmin):
    list_display = ('deposit_percentage',)