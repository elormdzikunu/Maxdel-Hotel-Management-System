from django.contrib.auth import authenticate, login # type: ignore
from django.contrib.auth.decorators import login_required, user_passes_test # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.shortcuts import render, redirect # type: ignore
from django.contrib import messages # type: ignore
from django.utils import timezone # type: ignore
from django.db import models # type: ignore
from django.db.models import Sum # type: ignore
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
from django.http import HttpResponse, JsonResponse # type: ignore
from datetime import timedelta, date
import os
import csv
import requests # type: ignore
import uuid

from .models import Booking, Room, HotelSettings


# =========================
# PAYSTACK CONFIGURATION
# =========================

PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
PAYSTACK_INITIALIZE_URL = 'https://api.paystack.co/transaction/initialize'
PAYSTACK_VERIFY_URL = 'https://api.paystack.co/transaction/verify'


# =========================
# HELPER FUNCTIONS
# =========================

def is_receptionist(user):
    return user.groups.filter(name="Receptionist").exists()


def is_md(user):
    return user.groups.filter(name="MD").exists()


def send_hotel_notification(subject, message):
    """Centralized email notification handler"""
    try:
        recipient = [settings.EMAIL_HOST_USER] if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER else ['admin@maxdelhotel.com']
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@maxdelhotel.com')
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient,
            fail_silently=False,
        )
    except Exception:
        pass


def search_bookings(queryset, search_query):
    """Centralized search filter helper for bookings"""
    if search_query:
        return queryset.filter(
            models.Q(guest_name__icontains=search_query) |
            models.Q(guest_phone__icontains=search_query) |
            models.Q(room__room_number__icontains=search_query)
        )
    return queryset


# =========================
# PUBLIC VIEWS
# =========================

def home(request):
    return render(request, "index.html")


def About(request):
    return render(request, "About.html")


def public_rooms(request):
    """Public page showing all room types with pictures and prices"""
    deluxe_rooms = Room.objects.filter(room_type='Deluxe', status='available')
    executive_rooms = Room.objects.filter(room_type='Executive', status='available')
    presidential_rooms = Room.objects.filter(room_type='Presidential', status='available')
    
    deluxe_price = deluxe_rooms.first().price_per_night if deluxe_rooms.exists() else 0
    executive_price = executive_rooms.first().price_per_night if executive_rooms.exists() else 0
    presidential_price = presidential_rooms.first().price_per_night if presidential_rooms.exists() else 0
    
    context = {
        'deluxe_rooms': deluxe_rooms,
        'executive_rooms': executive_rooms,
        'presidential_rooms': presidential_rooms,
        'deluxe_price': deluxe_price,
        'executive_price': executive_price,
        'presidential_price': presidential_price,
    }
    
    return render(request, "rooms.html", context)


def booking(request):
    rooms = Room.objects.filter(status='available')
    search_query = request.GET.get('search', '')
    
    if search_query:
        rooms = rooms.filter(room_number__icontains=search_query)

    if request.method == "POST":
        guest_name = request.POST.get("guest_name")
        guest_phone = request.POST.get("guest_phone")
        room_id = request.POST.get("room")
        check_in = request.POST.get("check_in")
        check_out = request.POST.get("check_out")

        room = Room.objects.get(id=room_id)

        booking_obj = Booking.objects.create(
            guest_name=guest_name,
            guest_phone=guest_phone,
            room=room,
            check_in=check_in,
            check_out=check_out
        )

        room.status = 'occupied'
        room.save()

        send_hotel_notification(
            subject=f'New Booking: Room {room.room_number}',
            message=f'NEW BOOKING - Guest: {guest_name}, Phone: {guest_phone}, Room: {room.room_number}, Check-in: {check_in}, Check-out: {check_out}'
        )

        messages.success(request, f"Room booked successfully! Your booking for Room {room.room_number} has been confirmed.")
        return redirect("home")

    hotel_settings = HotelSettings.get_settings()
    paystack_public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', os.environ.get('PAYSTACK_PUBLIC_KEY', ''))
    return render(request, "booking.html", {
        "rooms": rooms, 
        "hotel_settings": hotel_settings, 
        "paystack_public_key": paystack_public_key
    })


# =========================
# AUTHENTICATION
# =========================

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("post_login")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")


@login_required
def post_login(request):
    user = request.user
    if is_receptionist(user):
        return redirect("/secure-reception/dashboard/")
    if is_md(user):
        return redirect("/secure-md/dashboard/")
    return redirect("/secure-admin-login/")


# =========================
# DASHBOARDS
# =========================

@login_required
@user_passes_test(is_receptionist)
def reception_dashboard(request):
    today = timezone.now().date()
    search_query = request.GET.get('search', '')
    bookings = Booking.objects.filter(check_out__gte=today)
    
    bookings = search_bookings(bookings, search_query).select_related("room").order_by("-created_at")
    
    all_rooms = Room.objects.all().order_by("room_number")
    available_rooms = Room.objects.filter(status='available').count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    cleaning_rooms = Room.objects.filter(status='cleaning').count()
    maintenance_rooms = Room.objects.filter(status='maintenance').count()
    today_bookings = Booking.objects.filter(created_at__date=today).count()
    daily_revenue = Booking.objects.filter(created_at__date=today).aggregate(total=Sum('room__price_per_night'))['total'] or 0

    context = {
        "bookings": bookings,
        "all_rooms": all_rooms,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "cleaning_rooms": cleaning_rooms,
        "maintenance_rooms": maintenance_rooms,
        "today_bookings": today_bookings,
        "daily_revenue": daily_revenue,
        "search_query": search_query,
    }
    return render(request, "reception/dashboard.html", context)


@login_required
@user_passes_test(is_md)
def md_dashboard(request):
    today = timezone.now().date()
    search_query = request.GET.get('search', '')
    bookings = search_bookings(Booking.objects.select_related("room"), search_query).order_by("-created_at")[:50]
    
    total_rooms = Room.objects.count()
    total_bookings = Booking.objects.count()
    available_rooms = Room.objects.filter(status='available').count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    daily_revenue = Booking.objects.filter(created_at__date=today).aggregate(total=Sum('room__price_per_night'))['total'] or 0
    weekly_revenue = Booking.objects.filter(created_at__date__gte=today - timedelta(days=7)).aggregate(total=Sum('room__price_per_night'))['total'] or 0
    monthly_revenue = Booking.objects.filter(created_at__date__gte=today - timedelta(days=30)).aggregate(total=Sum('room__price_per_night'))['total'] or 0

    hotel_settings = HotelSettings.get_settings()
    rooms_list = Room.objects.all().order_by("room_number")

    context = {
        "bookings": bookings,
        "total_rooms": total_rooms,
        "total_bookings": total_bookings,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "daily_revenue": daily_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "search_query": search_query,
        "hotel_settings": hotel_settings,
        "rooms_list": rooms_list,
    }
    return render(request, "md/dashboard.html", context)


# =========================
# GUEST HISTORY
# =========================

@login_required
def guest_history(request):
    search_query = request.GET.get('guest', '')
    bookings = []
    if search_query:
        bookings = search_bookings(Booking.objects.all(), search_query).select_related("room").order_by("-created_at")
    return render(request, "md/guest_history.html", {"bookings": bookings, "search_query": search_query})


# =========================
# REPORTS
# =========================

@login_required
@user_passes_test(is_md)
def generate_report(request):
    """Generate CSV report of bookings"""
    report_type = request.GET.get('type', 'all')
    today = timezone.now().date()
    
    if report_type == 'daily':
        bookings = Booking.objects.filter(created_at__date=today)
        filename = f"daily_report_{today}.csv"
    elif report_type == 'weekly':
        bookings = Booking.objects.filter(created_at__date__gte=today - timedelta(days=7))
        filename = f"weekly_report_{today}.csv"
    elif report_type == 'monthly':
        bookings = Booking.objects.filter(created_at__date__gte=today - timedelta(days=30))
        filename = f"monthly_report_{today}.csv"
    elif report_type == 'yearly':
        bookings = Booking.objects.filter(created_at__date__gte=today - timedelta(days=365))
        filename = f"yearly_report_{today}.csv"
    else:
        bookings = Booking.objects.all()
        filename = f"all_bookings_report_{today}.csv"
    
    bookings = bookings.select_related("room")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Guest Name', 'Phone', 'Email', 'Room Number', 'Room Type', 'Check In', 'Check Out', 'Price/Night', 'Total Amount', 'Status', 'Date Created'])
    
    for b in bookings:
        writer.writerow([
            b.guest_name,
            b.guest_phone,
            b.guest_email or '',
            b.room.room_number,
            b.room.room_type,
            b.check_in,
            b.check_out,
            b.room.price_per_night,
            b.total_price,
            'Checked Out' if b.checked_out else 'Active',
            b.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@login_required
@user_passes_test(is_md)
def view_monthly_report(request):
    """View monthly report on screen"""
    month = request.GET.get('month')
    today = timezone.now().date()
    
    if month:
        year, month_num = map(int, month.split('-'))
        start_date = date(year, month_num, 1)
        if month_num == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month_num + 1, 1) - timedelta(days=1)
    else:
        start_date = date(today.year, today.month, 1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    bookings = Booking.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).select_related("room")
    total_revenue = sum(b.total_price for b in bookings)
    
    return render(request, "md/monthly_report.html", {
        'bookings': bookings,
        'total_revenue': total_revenue,
        'month': month or today.strftime('%Y-%m'),
        'start_date': start_date,
        'end_date': end_date
    })


@login_required
@user_passes_test(is_md)
def view_yearly_report(request):
    """View yearly report on screen"""
    year = int(request.GET.get('year', timezone.now().year))
    
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    bookings = Booking.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).select_related("room")
    total_revenue = sum(b.total_price for b in bookings)
    
    monthly_data = {}
    for m in range(1, 13):
        m_bookings = bookings.filter(created_at__month=m)
        m_revenue = sum(b.total_price for b in m_bookings)
        monthly_data[m] = {'count': m_bookings.count(), 'revenue': m_revenue}
    
    return render(request, "md/yearly_report.html", {
        'bookings': bookings,
        'total_revenue': total_revenue,
        'year': year,
        'monthly_data': monthly_data
    })


@csrf_exempt
@login_required
@user_passes_test(is_md)
def edit_room_price(request):
    """Edit room price"""
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        new_price = request.POST.get('price')
        next_url = request.POST.get('next', 'manage_rooms')
        room = Room.objects.get(id=room_id)
        room.price_per_night = new_price
        room.save()
        messages.success(request, f"Price for Room {room.room_number} updated to GH₵{new_price}")
        if next_url == 'md_dashboard':
            return redirect("md_dashboard")
        return redirect("manage_rooms")
    return redirect("manage_rooms")


@csrf_exempt
@login_required
@user_passes_test(is_md)
def update_hotel_settings(request):
    """Update global hotel settings (deposit percentage)"""
    if request.method == 'POST':
        deposit_percentage = request.POST.get('deposit_percentage')
        if deposit_percentage:
            try:
                pct = float(deposit_percentage)
                if 0 <= pct <= 100:
                    settings_obj = HotelSettings.get_settings()
                    settings_obj.deposit_percentage = pct
                    settings_obj.save()
                    messages.success(request, f"Booking deposit percentage successfully set to {pct}%")
                else:
                    messages.error(request, "Deposit percentage must be between 0 and 100.")
            except ValueError:
                messages.error(request, "Invalid number format for deposit percentage.")
    return redirect("md_dashboard")


# =========================
# CHECKOUT & ROOM STATUS
# =========================

@login_required
def checkout_booking(request, booking_id):
    booking_obj = Booking.objects.get(id=booking_id)
    booking_obj.checked_out = True
    booking_obj.save()
    room = booking_obj.room
    room.status = 'cleaning'
    room.save()
    messages.success(request, f"Guest {booking_obj.guest_name} checked out. Room {room.room_number} marked for housekeeping.")
    
    send_hotel_notification(
        subject=f'Room Checked Out: {room.room_number}',
        message=f'Room {room.room_number} has been checked out by {booking_obj.guest_name} and marked for cleaning.'
    )

    return redirect("reception_dashboard")


@csrf_exempt
@login_required
def update_room_status(request, room_id):
    """Update room status (available, occupied, cleaning, maintenance)"""
    if request.method == "POST":
        new_status = request.POST.get("status")
        room = Room.objects.get(id=room_id)
        if new_status in dict(Room.ROOM_STATUS):
            room.status = new_status
            room.save()
            messages.success(request, f"Room {room.room_number} status updated to '{room.get_status_display()}'")
    next_url = request.POST.get("next")
    if next_url == "reception":
        return redirect("reception_dashboard")
    return redirect("manage_rooms")


@csrf_exempt
@login_required
@user_passes_test(is_receptionist)
def reception_walkin_booking(request):
    """Register a walk-in guest directly from the reception desk"""
    if request.method == "POST":
        guest_name = request.POST.get("guest_name")
        guest_phone = request.POST.get("guest_phone")
        guest_email = request.POST.get("guest_email", "")
        room_id = request.POST.get("room_id")
        check_in = request.POST.get("check_in")
        check_out = request.POST.get("check_out")
        payment_status = request.POST.get("payment_status", "paid")
        amount_paid = request.POST.get("amount_paid", 0)

        try:
            room = Room.objects.get(id=room_id)
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)

            if not room.is_available_between(check_in_date, check_out_date):
                messages.error(request, f"Room {room.room_number} is unavailable for the selected dates due to an existing booking.")
                return redirect("reception_dashboard")

            nights = max((check_out_date - check_in_date).days, 1)
            total_amount = room.price_per_night * nights
            amount_paid_dec = float(amount_paid) if amount_paid else (float(total_amount) if payment_status == 'paid' else 0.0)
            balance_due = float(total_amount) - amount_paid_dec

            reference = f"WALKIN-{uuid.uuid4().hex[:10].upper()}"

            Booking.objects.create(
                guest_name=guest_name,
                guest_phone=guest_phone,
                guest_email=guest_email,
                room=room,
                check_in=check_in,
                check_out=check_out,
                payment_status=payment_status,
                payment_reference=reference,
                total_amount=total_amount,
                amount_paid=amount_paid_dec,
                deposit_amount=amount_paid_dec,
                balance_due=balance_due,
                payment_date=timezone.now() if payment_status == 'paid' else None
            )

            room.status = 'occupied'
            room.save()

            messages.success(request, f"Walk-in booking created for {guest_name} in Room {room.room_number}!")
        except Exception as e:
            messages.error(request, f"Failed to create booking: {str(e)}")

    return redirect("reception_dashboard")


def view_invoice(request, booking_id):
    """View & print guest invoice/receipt"""
    try:
        booking_obj = Booking.objects.select_related("room").get(id=booking_id)
        hotel_settings = HotelSettings.get_settings()
        nights = 1
        if booking_obj.check_in and booking_obj.check_out:
            nights = max((booking_obj.check_out - booking_obj.check_in).days, 1)

        context = {
            'booking': booking_obj,
            'nights': nights,
            'hotel_settings': hotel_settings,
        }
        return render(request, "invoice.html", context)
    except Booking.DoesNotExist:
        messages.error(request, "Booking invoice not found.")
        return redirect("home")


# =========================
# ROOM MANAGEMENT
# =========================

@login_required
@user_passes_test(is_md)
def manage_rooms(request):
    rooms = Room.objects.all().order_by("room_number")
    return render(request, "md/rooms.html", {"rooms": rooms})


@login_required
@user_passes_test(is_md)
def add_room(request):
    if request.method == "POST":
        room_number = request.POST.get("room_number")
        room_type = request.POST.get("room_type")
        price = request.POST.get("price")
        Room.objects.create(room_number=room_number, room_type=room_type, price_per_night=price)
        messages.success(request, "Room added successfully")
        return redirect("manage_rooms")
    return redirect("manage_rooms")


@login_required
@user_passes_test(is_md)
def toggle_room(request, room_id):
    room = Room.objects.get(id=room_id)
    room.status = 'maintenance' if room.status != 'maintenance' else 'available'
    room.save()
    return redirect("manage_rooms")


# =========================
# PAYSTACK PAYMENT
# =========================

@csrf_exempt
def initialize_payment(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        guest_name = data.get('guest_name')
        guest_phone = data.get('guest_phone')
        guest_email = data.get('guest_email')
        room_id = data.get('room_id')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        payment_type = data.get('payment_type', 'deposit')  # 'deposit' or 'full'
        
        try:
            room = Room.objects.get(id=room_id)
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
            if not room.is_available_between(check_in_date, check_out_date):
                return JsonResponse({'status': False, 'message': f'Room {room.room_number} is already booked for the selected dates.'}, status=400)

            nights = max((check_out_date - check_in_date).days, 1)
            nightly_rate = float(room.price_per_night)
            total_amount = nightly_rate * nights
            hotel_settings = HotelSettings.get_settings()
            deposit_rate = float(hotel_settings.deposit_percentage) / 100.0
            deposit_amount = total_amount * deposit_rate
            
            charge_amount = total_amount if payment_type == 'full' else deposit_amount
            amount_kobo = int(charge_amount * 100)
            reference = f"MAXDEL-{uuid.uuid4().hex[:12].upper()}"
            
            booking_obj = Booking.objects.create(
                guest_name=guest_name, guest_phone=guest_phone, guest_email=guest_email,
                room=room, check_in=check_in, check_out=check_out,
                payment_status='pending', payment_reference=reference,
                deposit_amount=deposit_amount, total_amount=total_amount, balance_due=total_amount - charge_amount
            )
            
            headers = {'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}', 'Content-Type': 'application/json'}
            callback_url = request.build_absolute_uri(f'/payment/callback/?reference={reference}')
            payload = {
                'email': guest_email, 
                'amount': amount_kobo, 
                'reference': reference,
                'callback_url': callback_url,
                'metadata': {
                    'booking_id': booking_obj.id, 
                    'guest_name': guest_name, 
                    'room_number': room.room_number,
                    'payment_type': payment_type,
                    'total_amount': total_amount,
                    'charge_amount': charge_amount
                }
            }
            
            response = requests.post(PAYSTACK_INITIALIZE_URL, json=payload, headers=headers)
            result = response.json()
            
            if result.get('status'):
                return JsonResponse({
                    'status': True, 
                    'authorization_url': result['data']['authorization_url'], 
                    'reference': reference,
                    'amount': amount_kobo
                })
            else:
                booking_obj.delete()
                return JsonResponse({'status': False, 'message': result.get('message', 'Payment init failed')}, status=400)
        except Room.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'Room not found'}, status=400)
        except Exception as e:
            return JsonResponse({'status': False, 'message': f'Server error: {str(e)}'}, status=500)
    return JsonResponse({'status': False, 'message': 'Only POST allowed'}, status=405)


def payment_callback(request):
    reference = request.GET.get('reference')
    if not reference:
        messages.error(request, "Payment reference not found")
        return redirect("booking")
    
    headers = {'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'}
    response = requests.get(f'{PAYSTACK_VERIFY_URL}/{reference}', headers=headers)
    result = response.json()
    
    if result.get('status') and result['data']['status'] == 'success':
        try:
            booking_obj = Booking.objects.get(payment_reference=reference)
            booking_obj.payment_status = 'paid'
            booking_obj.payment_date = timezone.now()
            booking_obj.save()
            room = booking_obj.room
            room.status = 'occupied'
            room.save()
            messages.success(request, f"Payment successful! Booking confirmed for Room {room.room_number}. Receipt # {booking_obj.id}")
            return redirect(f"/invoice/{booking_obj.id}/")
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found")
            return redirect("booking")
    else:
        try:
            booking_obj = Booking.objects.get(payment_reference=reference)
            booking_obj.payment_status = 'failed'
            booking_obj.save()
        except Exception:
            pass
        messages.error(request, "Payment failed. Please try again.")
        return redirect("booking")


@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        import json
        event = json.loads(request.body)
        if event.get('event') == 'charge.success':
            data = event.get('data', {})
            reference = data.get('reference')
            try:
                booking_obj = Booking.objects.get(payment_reference=reference)
                booking_obj.payment_status = 'paid'
                booking_obj.payment_date = timezone.now()
                booking_obj.save()
                room = booking_obj.room
                room.status = 'occupied'
                room.save()
            except Booking.DoesNotExist:
                pass
    return HttpResponse(status=200)
