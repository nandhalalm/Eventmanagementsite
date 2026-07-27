from django.db import models
from django.contrib.auth.models import User


# Event Table
class Event(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    venue = models.CharField(max_length=200)
    event_date = models.DateField()
    event_time = models.TimeField()
    last_date = models.DateField()
    description = models.TextField()
    image = models.ImageField(upload_to='events/')
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2)
    brochure = models.FileField(upload_to='brochures/', blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# Event Registration
class Registration(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=150)
    college = models.CharField(max_length=200)
    department = models.CharField(max_length=150)
    semester = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField()

    payment_status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


# Payment Details
class Payment(models.Model):
    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE
    )

    stripe_payment_id = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=30)

    def __str__(self):
        return self.stripe_payment_id


# Event Token
class Token(models.Model):
    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE
    )

    token_number = models.CharField(max_length=50, unique=True)
    seat_number = models.CharField(max_length=20)
    generated_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token_number


# Contact Form
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Gallery
class Gallery(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='gallery/')

    def __str__(self):
        return self.title