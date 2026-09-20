from django.urls import path # type: ignore
from . import views 

urlpatterns = [
    # Public Pages
    path('', views.home, name='home'),
    path('booking/', views.booking, name='booking'),
    path('About/', views.About, name='About'),
    
    # Admin Login (hidden path)
    path('secure-admin-login/', views.login_view, name='login'),
    path('secure-auth/', views.post_login, name='post_login'),
    
    # Admin Dashboard (protected)
    path('secure-md/dashboard/', views.md_dashboard, name='md_dashboard'),
    path('secure-reception/dashboard/', views.reception_dashboard, name='reception_dashboard'),
    path('secure-checkout/<int:booking_id>/', views.checkout_booking, name='checkout'),
    
    # Room Management & Status
    path('secure-md/rooms', views.manage_rooms, name='manage_rooms'),
    path('secure-md/rooms/add/', views.add_room, name='add_room'),
    path('secure-md/rooms/toggle/<int:room_id>/', views.toggle_room, name='toggle_room'),
    path('secure-room/status/<int:room_id>/', views.update_room_status, name='update_room_status'),
    path('secure-reception/walkin/', views.reception_walkin_booking, name='reception_walkin'),
    
    # Invoices & Receipts
    path('invoice/<int:booking_id>/', views.view_invoice, name='view_invoice'),
    
    # New Features (protected)
    path('secure-md/guest-history/', views.guest_history, name='guest_history'),
    path('secure-md/reports/', views.generate_report, name='generate_report'),
    
    # Paystack Payment
    path('payment/initialize/', views.initialize_payment, name='initialize_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/webhook/', views.payment_webhook, name='payment_webhook'),
    
    # Reports (view and download)
    path('secure-md/report/monthly/', views.view_monthly_report, name='view_monthly_report'),
    path('secure-md/report/yearly/', views.view_yearly_report, name='view_yearly_report'),
    path('secure-md/room/edit-price/', views.edit_room_price, name='edit_room_price'),
    path('secure-md/settings/update/', views.update_hotel_settings, name='update_settings'),
    
    # Public Rooms Page
    path('rooms/', views.public_rooms, name='public_rooms'),
]

