import os
import sys
import django
from django.utils import timezone
from io import BytesIO

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safecampus_main.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Incident, Message

User = get_user_model()
client = Client()

results = []

def ensure_user(username, role):
    user, _ = User.objects.get_or_create(username=username, defaults={'role': role, 'email': f'{username}@example.com'})
    user.set_password('password123')
    user.role = role
    user.is_active = True
    user.save()
    return user

# Create users
student = ensure_user('flow_student', 'student')
counsellor = ensure_user('flow_counsellor', 'counsellor')
admin = ensure_user('flow_admin', 'admin')

# Student files a report via IncidentReportForm simulated POST
client.login(username='flow_student', password='password123')
report_data = {
    'title': 'Flow Test Incident',
    'description': 'Testing full flow via automated script.',
    'location': 'Test Lab',
    'incident_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    'is_anonymous': 'on',
}
resp = client.post('/report/', report_data, follow=True)
results.append(('student_report_post_status', resp.status_code))

# Get the incident
inc = Incident.objects.filter(reporter=student).order_by('-reported_at').first()
if not inc:
    results.append(('incident_found', False))
else:
    results.append(('incident_found', True, inc.id, inc.case_token, inc.is_anonymous))

# Counsellor accesses counsellor dashboard
client.logout()
client.login(username='flow_counsellor', password='password123')
resp = client.get('/counsellor/')
results.append(('counsellor_dashboard_status', resp.status_code))

# Counsellor opens incident detail view
resp = client.get(f'/incident/{inc.id}/')
results.append(('counsellor_view_incident_get', resp.status_code))

# Counsellor posts a status update
resp = client.post(f'/incident/{inc.id}/', {'status': 'Under Review', 'internal_notes': 'Automated review.'}, follow=True)
results.append(('counsellor_status_update', resp.status_code))
inc.refresh_from_db()
results.append(('incident_status_now', inc.status))

# Counsellor posts a message (allowed even if reporter anonymous)
resp = client.post(f'/incident/{inc.id}/', {'message': 'Counsellor automated message.'}, follow=True)
results.append(('counsellor_message_post', resp.status_code))
msgs = Message.objects.filter(incident=inc)
results.append(('messages_count_after_counsellor', msgs.count()))

# Student tries to post message while anonymous (should be blocked)
client.logout()
client.login(username='flow_student', password='password123')
resp = client.post(f'/my-case/{inc.id}/chat/', {'message': 'Student trying to message while anonymous.'}, follow=True)
results.append(('student_message_while_anonymous_status', resp.status_code))
msgs = Message.objects.filter(incident=inc)
results.append(('messages_count_after_student_try', msgs.count()))

# Student reveals identity
resp = client.get(f'/reveal/{inc.id}/', follow=True)
results.append(('reveal_identity_status', resp.status_code))
inc.refresh_from_db()
results.append(('incident_identity_revealed', inc.is_identity_revealed))

# Student posts a message now
resp = client.post(f'/my-case/{inc.id}/chat/', {'message': 'Student message after reveal.'}, follow=True)
results.append(('student_message_after_reveal', resp.status_code))
msgs = Message.objects.filter(incident=inc)
results.append(('final_messages_count', msgs.count()))

# Admin tries to access admin_chat_view (should be allowed only for admin)
client.logout()
client.login(username='flow_admin', password='password123')
resp = client.get(f'/admin-chat/{inc.id}/')
results.append(('admin_chat_get_status', resp.status_code))

# Counsellor should NOT be able to access admin_chat_view
client.logout()
client.login(username='flow_counsellor', password='password123')
resp = client.get(f'/admin-chat/{inc.id}/', follow=True)
results.append(('counsellor_admin_chat_access', resp.status_code, 'redirected_to' in resp.redirect_chain[0][0] if resp.redirect_chain else None))

# Test export PDF endpoint (may return 500 if xhtml2pdf not installed)
client.logout()
client.login(username='flow_counsellor', password='password123')
resp = client.get(f'/incident/{inc.id}/export-pdf/')
results.append(('export_pdf_status', resp.status_code))

# SOS endpoint test: simulate audio upload
client.logout()
client.login(username='flow_student', password='password123')
from django.core.files.uploadedfile import SimpleUploadedFile
fake_audio = SimpleUploadedFile('voice.wav', b'RIFF....', content_type='audio/wav')
resp = client.post('/handle-sos/', {'audio_data': fake_audio})
results.append(('sos_post_status', resp.status_code))

# Print results
print('FULL FLOW TEST RESULTS:')
for r in results:
    print('-', r)

print('\nSummary:')
print('Check items: student report, counsellor actions, reveal identity, admin access, PDF export, SOS upload')
print('Script finished.')
