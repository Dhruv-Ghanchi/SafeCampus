import os
import sys
import django
from django.utils import timezone

# Ensure project root is on sys.path so Django settings module can be imported
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safecampus_main.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Incident

User = get_user_model()

# Create or get test users
counsellor, _ = User.objects.get_or_create(username='test_counsellor', defaults={'role': 'counsellor', 'email': 'counsellor@example.com'})
# Ensure password and role are set for test counsellor
counsellor.set_password('password123')
counsellor.role = 'counsellor'
counsellor.is_active = True
counsellor.save()

student, _ = User.objects.get_or_create(username='test_student', defaults={'role': 'student', 'email': 'student@example.com'})
# Ensure password and role are set for test student
student.set_password('password123')
student.role = 'student'
student.is_active = True
student.save()

# Create or get an incident reported by student
incident, created = Incident.objects.get_or_create(
    case_token='TST001',
    defaults={
        'title': 'Test Incident',
        'description': 'This is a test incident created by script.',
        'location': 'Campus',
        'incident_date': timezone.now(),
        'reporter': student,
        'is_anonymous': True,
        'is_identity_revealed': False,
        'status': 'New'
    }
)

print('Incident:', incident.id, incident.case_token, 'anonymous=', incident.is_anonymous)

# Use test client to login as counsellor and post status update + message
client = Client()
logged_in = client.login(username='test_counsellor', password='password123')
print('Counsellor logged in:', logged_in)

# POST status update
resp1 = client.post(f'/incident/{incident.id}/', {'status': 'Under Review', 'internal_notes': 'Reviewed by counsellor.'}, follow=True)
print('Status update response code:', resp1.status_code)

# POST a chat message as counsellor (should be allowed even if reporter anonymous)
resp2 = client.post(f'/incident/{incident.id}/', {'message': 'Hello, we are reviewing your case.'}, follow=True)
print('Message post response code:', resp2.status_code)

# Refresh incident
incident.refresh_from_db()
print('Incident new status:', incident.status)

# Verify message created
from core.models import Message
msgs = Message.objects.filter(incident=incident).order_by('created_at')
print('Messages count:', msgs.count())
for m in msgs:
    print('-', m.sender.username, m.text[:80])

print('Test script finished.')
