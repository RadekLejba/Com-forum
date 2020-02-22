from django import forms
from django.contrib.auth.forms import UserCreationForm


class ExtendedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Visible name")
