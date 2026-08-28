from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from django.db.models import Q, F
from django.db import transaction

from .models import Event

from .models import Event, Registration, Payment, Token, Contact, Gallery
from .forms import RegisterForm, EventRegistrationForm, ContactForm

from django.contrib.admin.views.decorators import staff_member_required

import random
import string

import stripe
from django.conf import settings

from datetime import timedelta
from django.utils import timezone


# HOME


def home(request):
    events = Event.objects.filter(status=True).order_by('event_date')[:6]
    gallery = Gallery.objects.all()[:6]

    return render(request, 'home.html', {
        'events': events,
        'gallery': gallery,
    })



# ABOUT


def about(request):
    return render(request, 'about.html')



# GALLERY


def gallery(request):
    gallery = Gallery.objects.all()

    return render(request, 'gallery.html', {
        'gallery': gallery
    })



# CONTACT


def contact(request):

    if request.method == "POST":

        form = ContactForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Message sent successfully.")
            return redirect('contact')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {
        'form': form
    })



# REGISTER


def register(request):

    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('user_dashboard')

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            messages.success(request, "Account created successfully.")
            return redirect('login')

    else:
        form = RegisterForm()

    return render(request, 'register.html', {
        'form': form
    })



# LOGIN


def user_login(request):

    if request.user.is_authenticated:

        if request.user.is_staff:
            return redirect('admin_dashboard')

        return redirect('user_dashboard')

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            messages.success(request, "Login Successful")

            if user.is_staff:
                return redirect('admin_dashboard')

            return redirect('user_dashboard')

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")



# LOGOUT


@login_required(login_url='login')
def user_logout(request):

    logout(request)

    messages.success(request, "Logged out successfully.")

    return redirect("home")


# USER DASHBOARD


@login_required(login_url='login')
def user_dashboard(request):

    total_events = Event.objects.filter(status=True).count()

    registrations = Registration.objects.filter(user=request.user)

    total_registered = registrations.count()

    total_paid = registrations.filter(payment_status='Paid').count()

    context = {
        'registrations': registrations,
        'total_events': total_events,
        'total_registered': total_registered,
        'total_paid': total_paid,
    }

    return render(request, 'user/dashboard.html', context)



# EVENT LIST


def event_list(request):

    events = Event.objects.filter(status=True).order_by('event_date')

    return render(request, 'user/events.html', {
        'events': events
    })



# EVENT DETAILS


def event_detail(request, id):

    event = get_object_or_404(Event, id=id)

    already_registered = False

    if request.user.is_authenticated:
        already_registered = Registration.objects.filter(
            user=request.user,
            event=event
        ).exists()

    context = {
        'event': event,
        'already_registered': already_registered,
    }

    return render(request, 'user/event_detail.html', context)



# REGISTER EVENT


@login_required(login_url='login')
def register_event(request, id):

    event = get_object_or_404(Event, id=id)

    if Registration.objects.filter(user=request.user, event=event).exists():

        messages.warning(request, "You have already registered for this event.")

        return redirect('my_registrations')

    # Block registration if the event is closed, sold out, or past its deadline
    if not event.status:
        messages.error(request, "Registration is closed for this event.")
        return redirect('event_detail', id=event.id)

    if event.last_date < timezone.now().date():
        messages.error(request, "The registration deadline for this event has passed.")
        return redirect('event_detail', id=event.id)

    if event.available_seats <= 0:
        messages.error(request, "Sorry, this event is sold out.")
        return redirect('event_detail', id=event.id)

    if request.method == "POST":

        form = EventRegistrationForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                # lock the row so two people can't grab the last seat at once
                locked_event = Event.objects.select_for_update().get(id=event.id)

                if (
                    not locked_event.status
                    or locked_event.available_seats <= 0
                    or locked_event.last_date < timezone.now().date()
                ):
                    messages.error(request, "Sorry, registration just closed for this event.")
                    return redirect('event_detail', id=event.id)

                registration = form.save(commit=False)

                registration.user = request.user
                registration.event = locked_event

                registration.save()

                Event.objects.filter(id=locked_event.id).update(
                    available_seats=F('available_seats') - 1
                )

            messages.success(request, "Registration Successful.")

            return redirect('my_registrations')

    else:

        form = EventRegistrationForm(initial={
            'full_name': request.user.get_full_name(),
            'email': request.user.email,
        })

    context = {
        'event': event,
        'form': form,
    }

    return render(request, 'user/register_event.html', context)



# MY REGISTRATIONS new
# MY REGISTRATIONS

@login_required(login_url='login')
def my_registrations(request):

    registrations = Registration.objects.filter(
        user=request.user
    ).order_by('-registration_date')

    for reg in registrations:
        reg.can_cancel = (timezone.now() - reg.registration_date) <= timedelta(days=7)

    return render(request,
                  'user/my_registrations.html',
                  {
                      'registrations': registrations
                  })


# CANCEL REGISTRATION

@login_required(login_url='login')
def cancel_registration(request, id):

    registration = get_object_or_404(
        Registration,
        id=id,
        user=request.user
    )

    if timezone.now() - registration.registration_date > timedelta(days=7):

        messages.error(request, "Cancellation window has closed. Registrations can only be cancelled within 1 week.")

        return redirect('my_registrations')

    with transaction.atomic():

        # only give the seat back if the event's registration deadline hasn't passed
        if registration.event.last_date >= timezone.now().date():
            Event.objects.filter(id=registration.event_id).update(
                available_seats=F('available_seats') + 1
            )

        registration.delete()

    messages.success(request, "Registration cancelled successfully.")

    return redirect('my_registrations')



# PROFILE


@login_required(login_url='login')
def profile(request):

    return render(request,
                  'user/profile.html')

@login_required(login_url='login')
def edit_profile(request):

    user = request.user

    if request.method == "POST":

        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')

        user.save()

        messages.success(request, "Profile Updated Successfully")

        return redirect('profile')

    return render(request, 'user/edit_profile.html', {
        'user': user
    })


# ADMIN DASHBOARD


@staff_member_required(login_url='login')
def admin_dashboard(request):

    total_events = Event.objects.count()
    total_students = User.objects.filter(is_staff=False).count()
    total_registrations = Registration.objects.count()
    total_payments = Payment.objects.count()

    recent_registrations = Registration.objects.order_by('-registration_date')[:5]

    context = {
        'total_events': total_events,
        'total_students': total_students,
        'total_registrations': total_registrations,
        'total_payments': total_payments,
        'recent_registrations': recent_registrations,
    }

    return render(request, 'admin/dashboard.html', context)



# CREATE EVENT


@staff_member_required(login_url='login')
def create_event(request):

    if request.method == "POST":

        Event.objects.create(

            title=request.POST.get('title'),
            category=request.POST.get('category'),
            venue=request.POST.get('venue'),
            event_date=request.POST.get('event_date'),
            event_time=request.POST.get('event_time'),
            last_date=request.POST.get('last_date'),
            description=request.POST.get('description'),
            image=request.FILES.get('image'),
            total_seats=request.POST.get('total_seats'),
            available_seats=request.POST.get('total_seats'),
            registration_fee=request.POST.get('registration_fee'),
            brochure=request.FILES.get('brochure'),
            status=True

        )

        messages.success(request, "Event Added Successfully")

        return redirect('admin_dashboard')

    return render(request, 'admin/create_event.html')



# MANAGE EVENTS


@staff_member_required(login_url='login')
def manage_events(request):

    events = Event.objects.all().order_by('-event_date')

    return render(request,
                  'admin/manage_events.html',
                  {
                      'events': events
                  })



# EDIT EVENT


@staff_member_required(login_url='login')
def edit_event(request, id):

    event = get_object_or_404(Event, id=id)

    if request.method == "POST":

        event.title = request.POST.get('title')
        event.category = request.POST.get('category')
        event.venue = request.POST.get('venue')
        event.event_date = request.POST.get('event_date')
        event.event_time = request.POST.get('event_time')
        event.last_date = request.POST.get('last_date')
        event.description = request.POST.get('description')
        event.total_seats = request.POST.get('total_seats')
        event.available_seats = request.POST.get('available_seats')
        event.registration_fee = request.POST.get('registration_fee')

        if request.FILES.get('image'):
            event.image = request.FILES['image']

        if request.FILES.get('brochure'):
            event.brochure = request.FILES['brochure']

        event.save()

        messages.success(request, "Event Updated Successfully")

        return redirect('manage_events')

    return render(request,
                  'admin/edit_event.html',
                  {
                      'event': event
                  })



# DELETE EVENT


@staff_member_required(login_url='login')
def delete_event(request, id):

    event = get_object_or_404(Event, id=id)

    event.delete()

    messages.success(request, "Event Deleted Successfully")

    return redirect('manage_events')


# VIEW REGISTRATIONS + SEARCH

@staff_member_required(login_url='login')
def view_registrations(request):

    query = request.GET.get('q', '').strip()

    registrations = Registration.objects.select_related(
        'user',
        'event'
    ).order_by('-registration_date')

    if query:
        registrations = registrations.filter(
            Q(full_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(college__icontains=query) |
            Q(department__icontains=query) |
            Q(semester__icontains=query) |
            Q(event__title__icontains=query) |
            Q(user__username__icontains=query)
        )

    return render(
        request,
        'admin/registrations.html',
        {
            'registrations': registrations,
            'query': query,
        }
    )


# VIEW PAYMENTS


@staff_member_required(login_url='login')
def view_payments(request):

    payments = Payment.objects.select_related(
        'registration'
    ).all()

    return render(request,
                  'admin/payments.html',
                  {
                      'payments': payments
                  })


# ATTENDANCE

@login_required(login_url='login')
def attendance(request):

    if not request.user.is_staff:
        return redirect('home')

    # MARK / UNMARK ATTENDANCE
    if request.method == 'POST':

        registration_id = request.POST.get('registration_id')

        registration = get_object_or_404(
            Registration,
            id=registration_id
        )

        # Toggle attendance
        registration.attendance = not registration.attendance
        registration.save()

        if registration.attendance:
            messages.success(
                request,
                registration.full_name + " marked as Present"
            )
        else:
            messages.warning(
                request,
                registration.full_name + " marked as Absent"
            )

        query = request.POST.get('q', '')

        if query:
            return redirect('/attendance/?q=' + query)

        return redirect('attendance')

    # SEARCH
    query = request.GET.get('q', '').strip()

    registrations = Registration.objects.select_related(
        'user',
        'event'
    ).all().order_by('-registration_date')

    if query:

        registrations = registrations.filter(
            Q(full_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(college__icontains=query) |
            Q(event__title__icontains=query)
        )

    return render(
        request,
        'admin/attendance.html',
        {
            'registrations': registrations,
            'query': query,
        }
    )
# REPORTS


@staff_member_required(login_url='login')
def reports(request):

    return render(request,
                  'admin/reports.html',
                  {
                      'events': Event.objects.count(),
                      'students': User.objects.filter(is_staff=False).count(),
                      'registrations': Registration.objects.count(),
                      'payments': Payment.objects.count(),
                  })


# MESSAGES


@staff_member_required(login_url='login')
def messages_page(request):

    contacts = Contact.objects.all().order_by('-created_at')

    return render(request,
                  'admin/messages.html',
                  {
                      'contacts': contacts
                  })

@login_required(login_url='login')
@login_required(login_url='login')
def payment(request, id):

    registration = get_object_or_404(
        Registration,
        id=id,
        user=request.user
    )

    checkout_session = stripe.checkout.Session.create(

        payment_method_types=['card'],

        line_items=[

            {

                'price_data': {

                    'currency': 'inr',

                    'unit_amount': int(
                        registration.event.registration_fee * 100
                    ),

                    'product_data': {

                        'name': registration.event.title,

                    },

                },

                'quantity': 1,

            },

        ],

        mode='payment',

        success_url=settings.DOMAIN +
        '/payment-success/' +
        str(registration.id),

        cancel_url=settings.DOMAIN +
        '/payment-cancel/',

    )

    return redirect(checkout_session.url)

@login_required(login_url='login')
def payment_success(request, id):

    registration = get_object_or_404(
        Registration,
        id=id,
        user=request.user
    )

    if not Payment.objects.filter(
        registration=registration
    ).exists():

        Payment.objects.create(

            registration=registration,

            stripe_payment_id="Stripe",

            amount=registration.event.registration_fee,

            payment_status="Paid"

        )

        registration.payment_status = "Paid"

        registration.save()

        Token.objects.create(

            registration=registration,

            token_number="EVT" +
            ''.join(random.choices(
                string.ascii_uppercase +
                string.digits,
                k=6
            )),

            seat_number="S-" +
            str(random.randint(
                1,
                registration.event.total_seats
            ))

        )

    return redirect("ticket", registration.id)

@login_required(login_url='login')
def payment_cancel(request):

    messages.error(request, "Payment Cancelled")

    return redirect("my_registrations")


@login_required(login_url='login')
def ticket(request, id):

    registration = get_object_or_404(
        Registration,
        id=id,
        user=request.user
    )

    payment = Payment.objects.filter(
        registration=registration
    ).first()

    token = Token.objects.filter(
        registration=registration
    ).first()

    return render(
        request,
        "user/ticket.html",
        {
            "registration": registration,
            "payment": payment,
            "token": token,
        }
    )

#payment
stripe.api_key = settings.STRIPE_SECRET_KEY

# user search
def search_events(request):
    query = request.GET.get('q', '').strip()

    events = Event.objects.filter(status=True)

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(category__icontains=query) |
            Q(venue__icontains=query) |
            Q(description__icontains=query)
        )

    context = {
        'events': events,
        'query': query,
    }

    return render(request, 'search_results.html', context)