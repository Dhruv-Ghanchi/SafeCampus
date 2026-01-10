from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Incident, User

class UserRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('role', 'email')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs.update({'class': 'w-full p-3 border rounded-lg'})

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ['title', 'description', 'location', 'incident_date', 'evidence', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'incident_date': forms.DateTimeInput(attrs={'class': 'w-full p-3 border rounded-lg', 'type': 'datetime-local'}),
            'evidence': forms.FileInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
        }