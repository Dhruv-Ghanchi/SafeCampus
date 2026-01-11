from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import Incident, User, Message

class UserRegistrationForm(UserCreationForm):
    # Custom email field to ensure it's required and styled
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'w-full p-3 border rounded-lg', 'placeholder': 'Email Address'})
    )

    # Password complexity validator
    password_validator = RegexValidator(
        regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$',
        message="Password must be at least 6 characters long and include: 1 uppercase, 1 lowercase, 1 number, and 1 special character."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply styling to all fields automatically
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'w-full p-3 border rounded-lg'})
        
        # Apply the complex validator to the password field
        if 'password1' in self.fields:
            self.fields['password1'].validators.append(self.password_validator)

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = Incident
        # Added 'voice_recording' to support the SOS fallback logic
        fields = ['title', 'description', 'location', 'incident_date', 'evidence', 'voice_recording', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg', 'placeholder': 'Brief title of incident'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 3, 'placeholder': 'Describe what happened...'}),
            'location': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg', 'placeholder': 'e.g. Library, Block C, Parking'}),
            'incident_date': forms.DateTimeInput(attrs={'class': 'w-full p-3 border rounded-lg', 'type': 'datetime-local'}),
            'evidence': forms.FileInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'voice_recording': forms.FileInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
        }

    def clean_evidence(self):
        file = self.cleaned_data.get('evidence')
        if file:
            from django.conf import settings
            if file.size > getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024):
                raise forms.ValidationError('File too large (max 5 MB).')
            if file.content_type not in getattr(settings, 'ALLOWED_UPLOAD_CONTENT_TYPES', []):
                raise forms.ValidationError('Unsupported file type.')
        return file

    def clean_voice_recording(self):
        file = self.cleaned_data.get('voice_recording')
        if file:
            from django.conf import settings
            if file.size > getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024):
                raise forms.ValidationError('Recording too large (max 5 MB).')
            if file.content_type not in getattr(settings, 'ALLOWED_UPLOAD_CONTENT_TYPES', []):
                raise forms.ValidationError('Unsupported audio format.')
        return file

# --- LATEST ADDITION: MESSAGE FORM ---
class MessageForm(forms.ModelForm):
    """Form to handle chat messages and file attachments in the communication tunnel."""
    class Meta:
        model = Message
        fields = ['text', 'attachment']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500', 
                'rows': 2, 
                'placeholder': 'Type your message here...'
            }),
            'attachment': forms.FileInput(attrs={'class': 'hidden', 'id': 'file-upload'}),
        }

    def clean_attachment(self):
        file = self.cleaned_data.get('attachment')
        if file:
            from django.conf import settings
            if file.size > getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024):
                raise forms.ValidationError('Attachment too large (max 5 MB).')
            if file.content_type not in getattr(settings, 'ALLOWED_UPLOAD_CONTENT_TYPES', []):
                raise forms.ValidationError('Unsupported attachment type.')
        return file