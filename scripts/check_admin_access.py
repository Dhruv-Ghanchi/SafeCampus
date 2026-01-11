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

# Ensure test users exist
counsellor, _ = User.objects.get_or_create(username='flow_counsellor', defaults={'role': 'counsellor', 'email': 'flow_counsellor@example.com'})
counsellor.set_password('password123')
counsellor.role = 'counsellor'
counsellor.save()

admin, _ = User.objects.get_or_create(username='flow_admin', defaults={'role': 'admin', 'email': 'flow_admin@example.com'})
admin.set_password('password123')
admin.role = 'admin'
admin.save()

# Find an incident id
from core.models import Incident
inc = Incident.objects.first()
if not inc:
    print('NO_INCIDENT')
    sys.exit(1)

client = Client()
# Counsellor access
client.login(username='flow_counsellor', password='password123')
resp = client.get(f'/admin-chat/{inc.id}/')
print('counsellor_status', resp.status_code)

# Admin access
client.logout()
client.login(username='flow_admin', password='password123')
resp = client.get(f'/admin-chat/{inc.id}/')
print('admin_status', resp.status_code)
