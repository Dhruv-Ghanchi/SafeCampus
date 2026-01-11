import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safecampus_main.settings')
import django
django.setup()

from core.models import Incident
inc = Incident.objects.order_by('-reported_at').first()
print(inc.id if inc else 'NO_INCIDENT')
