from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from myapp import views

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Public Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search_events, name='search_events'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Password Reset (Used by {% url 'password_reset' %} in login template)
    path(
    'password-reset/',
    views.LocalPasswordResetView.as_view(),
    name='password_reset',
),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),

    # User Dashboard & Events
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:id>/', views.event_detail, name='event_detail'),
    path('register-event/<int:id>/', views.register_event, name='register_event'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('registration/cancel/<int:id>/', views.cancel_registration, name='cancel_registration'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Payments & Tickets
    path('payment/<int:id>/', views.payment, name='payment'),
    path('payment-success/<int:id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('ticket/<int:id>/', views.ticket, name='ticket'),

    # Custom Admin / Staff Panel
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-events/', views.manage_events, name='manage_events'),
    path('create-event/', views.create_event, name='create_event'),
    path('edit-event/<int:id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:id>/', views.delete_event, name='delete_event'),
    path('registrations/', views.view_registrations, name='view_registrations'),
    path('view-payments/', views.view_payments, name='view_payments'),
    path('attendance/', views.attendance, name='attendance'),
    path('reports/', views.reports, name='reports'),
    path('messages/', views.messages_page, name='messages'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)