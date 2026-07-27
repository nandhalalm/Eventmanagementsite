from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Event, Registration, Payment, Token, Contact, Gallery
from .forms import RegisterForm, EventRegistrationForm, ContactForm

from django.contrib.admin.views.decorators import staff_member_required

import random
import string

import stripe
from django.conf import settings


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

    if request.method == "POST":

        form = EventRegistrationForm(request.POST)

        if form.is_valid():

            registration = form.save(commit=False)

            registration.user = request.user
            registration.event = event

            registration.save()

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



# MY REGISTRATIONS


@login_required(login_url='login')
def my_registrations(request):

    registrations = Registration.objects.filter(
        user=request.user
    ).order_by('-registration_date')

    return render(request,
                  'user/my_registrations.html',
                  {
                      'registrations': registrations
                  })



# PROFILE


@login_required(login_url='login')
def profile(request):

    return render(request,
                  'user/profile.html')


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


# VIEW REGISTRATIONS


@staff_member_required(login_url='login')
def view_registrations(request):

    registrations = Registration.objects.select_related(
        'user',
        'event'
    ).order_by('-registration_date')

    return render(request,
                  'admin/registrations.html',
                  {
                      'registrations': registrations
                  })


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


@staff_member_required(login_url='login')
def attendance(request):

    registrations = Registration.objects.filter(
        payment_status="Paid"
    )

    return render(request,
                  'admin/attendance.html',
                  {
                      'registrations': registrations
                  })


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