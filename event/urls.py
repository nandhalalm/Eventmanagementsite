from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from myapp import views

urlpatterns = [

    # Django Admin
    path('admin/', admin.site.urls),

    # Public Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # User Dashboard
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:id>/', views.event_detail, name='event_detail'),
    path('register-event/<int:id>/', views.register_event, name='register_event'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('payment/<int:id>/', views.payment, name='payment'),
    path('ticket/<int:id>/', views.ticket, name='ticket'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('registration/cancel/<int:id>/', views.cancel_registration, name='cancel_registration'),

    # Custom Admin Panel
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:id>/', views.delete_event, name='delete_event'),
    path('registrations/', views.view_registrations, name='view_registrations'),
    path('payment/<int:id>/', views.payment, name='payment'),
    path('attendance/', views.attendance, name='attendance'),
    path('reports/', views.reports, name='reports'),
    path('messages/', views.messages_page, name='messages'),

    path("ticket/<int:id>/", views.ticket, name="ticket"),
    path('view-payments/', views.view_payments, name='view_payments'),

    path('manage-events/', views.manage_events, name='manage_events'),
    path('search/', views.search_events, name='search_events'),

    path(
    'payment-success/<int:id>/',
    views.payment_success,
    name='payment_success'
),

path(
    'payment-cancel/',
    views.payment_cancel,
    name='payment_cancel'
),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)