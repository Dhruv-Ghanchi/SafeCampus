from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('counsellor', 'Counsellor'),
        ('admin', 'Admin'),
        ('security', 'Security Staff'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.username} ({self.role})"

class Incident(models.Model):
    STATUS_CHOICES = (
        ('New', 'New'),
        ('Under Review', 'Under Review'),
        ('Action Taken', 'Action Taken'),
        ('Resolved', 'Resolved'),
    )
    
    # SOS & ML Fields
    voice_recording = models.FileField(upload_to='sos_recordings/', null=True, blank=True)
    is_emergency = models.BooleanField(default=False)
    sentiment_score = models.FloatField(default=0.0)
    case_token = models.CharField(max_length=10, unique=True, null=True, blank=True)
    
    # Core Fields
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    incident_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    
    # Evidence & Identity
    evidence = models.FileField(upload_to='evidence/%Y/%m/%d/', null=True, blank=True)
    internal_notes = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    is_identity_revealed = models.BooleanField(default=False)
    
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-is_emergency', '-updated_at']

    def __str__(self):
        return f"{self.case_token} - {self.title}"

class Message(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"