from django import forms
from django.contrib.auth.forms import UserCreationForm
from durationwidget.widgets import TimeDurationWidget

from users.models import Ban


class ExtendedUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Visible name", required=True, max_length=15)


class CustomBanForm(forms.ModelForm):
    duration = forms.DurationField(
        widget=TimeDurationWidget(show_minutes=False, show_seconds=False)
    )

    class Meta:
        model = Ban
        fields = ["user", "reason", "duration"]
