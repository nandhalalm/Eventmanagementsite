from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Registration, Contact


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password'
        ]


class LoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class EventRegistrationForm(forms.ModelForm):

    class Meta:
        model = Registration
        exclude = ['user', 'event', 'payment_status']


class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = '__all__'