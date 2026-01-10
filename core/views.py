from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from .models import Incident, User, Message
from .forms import IncidentReportForm, UserRegistrationForm
import random
import string
import datetime
from textblob import TextBlob

# --- 1. SOS UTILITIES ---

def generate_token():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_ai_empathy_note(sentiment_score):
    if sentiment_score <= -0.6:
        return "We detect you are in significant distress. Please know that we have prioritized your case immediately. Help is on the way."
    elif sentiment_score < 0:
        return "Thank you for sharing this. We understand this is a difficult time. A counsellor will reach out to you very soon."
    return "Thank you for your report. We appreciate you helping us keep the campus safe."

@login_required
def handle_sos_recording(request):
    if request.method == 'POST' and request.FILES.get('audio_data'):
        audio_file = request.FILES.get('audio_data')
        incident = Incident.objects.create(
            reporter=request.user,
            title="EMERGENCY SOS VOICE LOG",
            description="Voice recording submitted via SOS button fallback (Live Voicemail).",
            location="Live Location Triggered",
            incident_date=datetime.datetime.now(),
            case_token=generate_token(),
            sentiment_score=-1.0, 
            status='Under Review',
            is_emergency=True,
            voice_recording=audio_file
        )
        return JsonResponse({'status': 'success', 'case_token': incident.case_token})
    return JsonResponse({'status': 'failed'}, status=400)


# --- 2. ML SENTIMENT LOGIC ---

def calculate_advanced_sentiment(text):
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    critical_keywords = ['emergency', 'danger', 'hurt', 'threat', 'suicide', 'attack', 'weapon', 'police', 'urgent', 'rape', 'assault']
    high_risk_keywords = ['harass', 'stalk', 'scared', 'follow', 'touch', 'abuse', 'violence']
    text_lower = text.lower()
    for word in critical_keywords:
        if word in text_lower:
            return -1.0
    for word in high_risk_keywords:
        if word in text_lower:
            score -= 0.2
    return max(min(score, 1.0), -1.0)


# --- 3. AUTHENTICATION ---

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else: 
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    django_logout(request)
    return redirect('login')

@login_required
def home(request):
    if request.user.role == 'admin' or request.user.is_superuser: 
        return redirect('admin_dashboard')
    elif request.user.role in ['counsellor', 'security']: 
        return redirect('counsellor_dashboard')
    return redirect('student_dashboard')


# --- 4. INCIDENT REPORTING ---

@login_required
def report_incident(request):
    helplines = [
        {"name": "Women Helpline", "number": "1091", "icon": "📞"},
        {"name": "Police Emergency", "number": "100", "icon": "🚓"},
        {"name": "Campus Security", "number": "+91 98765 43210", "icon": "🛡️"},
        {"name": "Counselling Cell", "number": "011-2345678", "icon": "🧠"}
    ]
    if request.method == 'POST':
        form = IncidentReportForm(request.POST, request.FILES) 
        if form.is_valid():
            incident = form.save(commit=False)
            incident.case_token = generate_token()
            incident.sentiment_score = calculate_advanced_sentiment(incident.description)
            is_critical = False
            if incident.sentiment_score <= -0.6:
                incident.status = 'Under Review'
                is_critical = True
                incident.is_emergency = True
                incident.internal_notes = "SYSTEM ALERT: High distress detected. Auto-escalated via ML."
            incident.reporter = request.user
            incident.save()
            return render(request, 'core/success.html', {
                'incident': incident, 
                'is_critical': is_critical, 
                'helplines': helplines,
                'ai_note': get_ai_empathy_note(incident.sentiment_score)
            })
    else: 
        form = IncidentReportForm()
    return render(request, 'core/report_form.html', {'form': form})


# --- 5. DASHBOARDS ---

@login_required
def student_dashboard(request):
    reports = Incident.objects.filter(reporter=request.user).order_by('-reported_at')
    return render(request, 'core/student_dashboard.html', {'reports': reports})

@login_required
def counsellor_dashboard(request):
    if request.user.role not in ['counsellor', 'security'] and not request.user.is_superuser: 
        return redirect('home')
    incidents = Incident.objects.all().order_by('-is_emergency', 'sentiment_score')
    return render(request, 'core/counsellor_dashboard.html', {'incidents': incidents})

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    
    all_reports = Incident.objects.all().order_by('-reported_at')
    status_counts = all_reports.values('status').annotate(count=Count('id'))
    
    # FETCH STAFF LIST (Counsellors & Security)
    staff_members = User.objects.filter(role__in=['counsellor', 'security']).order_by('role')

    context = {
    'incidents': all_reports,
    'staff_members': User.objects.filter(role__in=['counsellor', 'security']),
    'students': User.objects.filter(role='student'), # ADD THIS LINE
    'student_count': User.objects.filter(role='student').count(),
    'counsellor_count': User.objects.filter(role__in=['counsellor', 'security']).count(),
    'total_reports': all_reports.count(),
    'avg_sentiment': round(all_reports.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0, 2),
    'status_data': list(status_counts),
    }
    return render(request, 'core/admin_dashboard.html', context)


# --- 6. CHAT & DETAILS ---

@login_required
def view_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    if request.method == 'POST':
        if 'status' in request.POST:
            incident.status = request.POST.get('status')
            incident.internal_notes = request.POST.get('internal_notes', '')
            incident.save()
        elif 'message' in request.POST:
            Message.objects.create(incident=incident, sender=request.user, text=request.POST.get('message'))
        return redirect('view_incident', incident_id=incident.id)
    return render(request, 'core/view_incident.html', {'incident': incident})

@login_required
def student_incident_detail(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id, reporter=request.user)
    if request.method == 'POST':
        text = request.POST.get('message')
        if text:
            Message.objects.create(incident=incident, sender=request.user, text=text)
            return redirect('student_incident_detail', incident_id=incident.id)
    return render(request, 'core/student_incident_detail.html', {'incident': incident})

@login_required
def reveal_identity(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id, reporter=request.user)
    incident.is_anonymous = False
    incident.is_identity_revealed = True
    incident.save()
    messages.success(request, "Identity revealed! You can now start the discussion.")
    return redirect('student_incident_detail', incident_id=incident.id)

def resources_view(request):
    return render(request, 'core/resources.html')


@login_required
def admin_view_chat(request, incident_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
    incident = get_object_or_404(Incident, id=incident_id)
    # Fetch all messages linked to this incident to display in the admin chat monitor
    messages = Message.objects.filter(incident=incident).order_by('timestamp')
    return render(request, 'core/admin_chat_view.html', {'incident': incident, 'messages': messages})