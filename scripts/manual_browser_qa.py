import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safecampus_main.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
client = Client()

# Ensure users exist
def ensure_user(username, role):
    user, _ = User.objects.get_or_create(username=username, defaults={'role': role, 'email': f'{username}@example.com'})
    user.set_password('password123')
    user.role = role
    user.is_active = True
    user.save()
    return user

student = ensure_user('manual_student', 'student')
counsellor = ensure_user('manual_counsellor', 'counsellor')
admin = ensure_user('manual_admin', 'admin')

snapshots_dir = os.path.join(BASE_DIR, '__manual_snapshots')
if not os.path.exists(snapshots_dir):
    os.makedirs(snapshots_dir)

results = []

def save_snapshot(name, content):
    path = os.path.join(snapshots_dir, name)
    with open(path, 'wb') as f:
        if isinstance(content, str):
            content = content.encode('utf-8')
        f.write(content)
    return path

# Anonymous root
resp = client.get('/')
results.append(('root_status', resp.status_code))
save_snapshot('root.html', resp.content)

# Student flow: login, dashboard, report page
client.login(username='manual_student', password='password123')
resp = client.get('/student/dashboard/')
results.append(('student_dashboard', resp.status_code))
save_snapshot('student_dashboard.html', resp.content)

resp = client.get('/report/')
results.append(('report_page', resp.status_code))
save_snapshot('report_page.html', resp.content)
client.logout()

# Counsellor flow
client.login(username='manual_counsellor', password='password123')
resp = client.get('/counsellor/')
results.append(('counsellor_dashboard', resp.status_code))
save_snapshot('counsellor_dashboard.html', resp.content)
client.logout()

# Admin flow
client.login(username='manual_admin', password='password123')
resp = client.get('/admin-portal/')
results.append(('admin_portal', resp.status_code))
save_snapshot('admin_portal.html', resp.content)
client.logout()

# Try viewing the latest incident as counsellor
from core.models import Incident
inc = Incident.objects.order_by('-reported_at').first()
if inc:
    client.login(username='manual_counsellor', password='password123')
    resp = client.get(f'/incident/{inc.id}/')
    results.append(('counsellor_view_incident', resp.status_code))
    save_snapshot(f'view_incident_{inc.id}.html', resp.content)
    client.logout()
else:
    results.append(('no_incident_found', True))

# Admin-chat access check
if inc:
    client.login(username='manual_counsellor', password='password123')
    resp = client.get(f'/admin-chat/{inc.id}/')
    results.append(('counsellor_admin_chat', resp.status_code))
    client.logout()
    client.login(username='manual_admin', password='password123')
    resp2 = client.get(f'/admin-chat/{inc.id}/')
    results.append(('admin_admin_chat', resp2.status_code))
    client.logout()

# Save results summary
summary_path = os.path.join(snapshots_dir, 'summary.txt')
with open(summary_path, 'w') as f:
    for r in results:
        f.write(str(r) + '\n')

print('Manual browser-like QA complete. Snapshots saved to:', snapshots_dir)
for r in results:
    print('-', r)
