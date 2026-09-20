from django.db import models # type: ignore

# Create your models here.
class Room(models.Model):
    ROOM_TYPES = [
      ("Deluxe","Deluxe"),
      ("Executive","Executive"),
      ("Presidential","Presidential"),               
    ]
    ROOM_STATUS = [
      ("available", "Available"),
      ("occupied", "Occupied"),
      ("cleaning", "Needs Cleaning"),
      ("maintenance", "Under Maintenance"),
    ]
    room_number = models.CharField(max_length=10,unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default="available")

    @property
    def is_available(self):
        return self.status == "available"

    def __str__(self):
        return f"Room{self.room_number} - ({self.room_type})" 

    def is_available_between(self, check_in_date, check_out_date):
        if self.status == 'maintenance':
            return False
        overlapping_bookings = Booking.objects.filter(
            room=self,
            checked_out=False,
            check_in__lt=check_out_date,
            check_out__gt=check_in_date
        )
        return not overlapping_bookings.exists()

    
    
class Booking(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    guest_name = models.CharField(max_length=100)
    guest_phone = models.CharField(max_length=20)
    guest_email = models.EmailField(blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    checked_out = models.BooleanField(default=False)
    
    # Payment fields
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    deposit_paid = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.guest_name} ({self.room.room_number})"
    
    @property
    def total_price(self):
        from datetime import date
        if self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            return self.room.price_per_night * nights
        return 0


class HotelSettings(models.Model):
    deposit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

    def __str__(self):
        return f"Hotel Settings (Deposit: {self.deposit_percentage}%)"

    