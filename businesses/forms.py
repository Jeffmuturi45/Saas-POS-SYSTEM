# businesses/forms.py
from django import forms
from .models import Business


class BusinessEditForm(forms.ModelForm):
    """Form for editing business details."""

    class Meta:
        model = Business
        fields = [
            'name', 'business_type', 'email', 'phone', 'address',
            'city', 'country', 'currency', 'timezone', 'status',
            'primary_color', 'secondary_color'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
        }
