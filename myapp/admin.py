from django.contrib import admin
from .models import *


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'venue',
        'event_date',
        'available_seats',
        'registration_fee',
        'status',
    )

    list_filter = ('category', 'status')
    search_fields = ('title', 'venue')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'college',
        'event',
        'payment_status',
        'registration_date',
    )

    list_filter = ('payment_status',)
    search_fields = ('full_name', 'college')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'registration',
        'amount',
        'payment_status',
        'payment_date',
    )

    search_fields = ('stripe_payment_id',)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = (
        'token_number',
        'registration',
        'seat_number',
        'generated_date',
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'subject',
        'created_at',
    )

    search_fields = ('name', 'email')


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
    )