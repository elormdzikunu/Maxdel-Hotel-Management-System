import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Apk.settings')
import django
django.setup()

from website.models import Room, Booking

Booking.objects.all().delete()
Room.objects.all().delete()

rooms = [
    ('101', 'Deluxe', 350),
    ('102', 'Deluxe', 350),
    ('103', 'Executive', 550),
    ('104', 'Presidential', 1200),
    ('201', 'Deluxe', 350),
    ('301', 'Executive', 550),
    ('401', 'Presidential', 1200),
    ('501', 'Deluxe', 380),
]

for number, room_type, price in rooms:
    Room.objects.get_or_create(
        room_number=number,
        defaults={'room_type': room_type, 'price_per_night': price}
    )

available = Room.objects.filter(is_available=True).count()
total = Room.objects.count()
print(f"SUCCESS! Added {total} rooms. {available} available.")
print("Room numbers:", list(Room.objects.values_list('room_number', flat=True)))
