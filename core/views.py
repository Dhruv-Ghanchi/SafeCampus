import random
import string
import datetime
from textblob import TextBlob
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.template.loader import get_template

# Ensure xhtml2pdf is imported if used in export
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

from .models import Incident, User, Message
from django.utils import timezone
from datetime import timedelta
from .forms import IncidentReportForm, UserRegistrationForm


def _is_duplicate_attachment(incident, sender, uploaded_file, window_seconds=30):
    """Return True if a recent message by sender for this incident has an
    attachment with the same original filename and size.
    """
    if not uploaded_file:
        return False
    recent_cutoff = timezone.now() - timedelta(seconds=window_seconds)
    candidates = Message.objects.filter(
        incident=incident,
        sender=sender,
        created_at__gte=recent_cutoff
    ).exclude(attachment='')[:20]

    import hashlib

    fname = getattr(uploaded_file, 'name', '')
    fsize = getattr(uploaded_file, 'size', None)

    # compute uploaded file hash (seek back after reading)
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    try:
        uploaded_bytes = uploaded_file.read()
        uploaded_hash = hashlib.sha256(uploaded_bytes).hexdigest() if uploaded_bytes is not None else None
    except Exception:
        uploaded_hash = None
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    for m in candidates:
        try:
            existing_name = getattr(m.attachment, 'name', '')
            existing_fname = existing_name.split('/')[-1] if existing_name else ''
            existing_size = None
            try:
                existing_size = m.attachment.size
            except Exception:
                existing_size = None

            # Try size+name quick match
            if existing_fname and fname and existing_fname == fname and existing_size is not None and fsize is not None and existing_size == fsize:
                return True

            # Fallback: compare content hash when available
            if uploaded_hash:
                try:
                    m.attachment.open('rb')
                    existing_bytes = m.attachment.read()
                    m.attachment.close()
                    existing_hash = hashlib.sha256(existing_bytes).hexdigest() if existing_bytes is not None else None
                    if existing_hash and existing_hash == uploaded_hash:
                        return True
                except Exception:
                    # ignore issues reading existing file
                    pass
        except Exception:
            continue
    return False

# --- 1. SOS UTILITIES ---

def generate_token():
    """Generates a unique 6-character case token."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_ai_empathy_note(sentiment_score):
    """Provides dynamic AI feedback based on incident sentiment."""
    if sentiment_score <= -0.6:
        return "We detect you are in significant distress. Please know that we have prioritized your case immediately. Help is on the way."
    elif sentiment_score < 0:
        return "Thank you for sharing this. We understand this is a difficult time. A counsellor will reach out to you very soon."
    return "Thank you for your report. We appreciate you helping us keep the campus safe."

@login_required
def handle_sos_recording(request):
    """AJAX endpoint to handle emergency voice recordings."""
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
            status='New', 
            is_emergency=True,
            voice_recording=audio_file
        )
        return JsonResponse({'status': 'success', 'case_token': incident.case_token})
    return JsonResponse({'status': 'failed'}, status=400)

# --- 2. ML SENTIMENT LOGIC ---

def calculate_advanced_sentiment(text):
    """Calculates sentiment and checks for critical keywords to set priority."""
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    critical_keywords = ['emergency', 'danger', 'hurt', 'threat', 'suicide', 'attack', 'weapon', 'police', 'urgent', 'rape', 'assault', 'kill']
    high_risk_keywords = ['harass', 'stalk', 'scared', 'follow', 'touch', 'abuse', 'violence']
    
    text_lower = text.lower()
    for word in critical_keywords:
        if word in text_lower:
            return -1.0
    for word in high_risk_keywords:
        if word in text_lower:
            score -= 0.3
            
    return max(min(score, 1.0), -1.0)

# --- 3. AUTHENTICATION & ROUTING ---

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
    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role in ['counsellor', 'security']:
        return redirect('counsellor_dashboard')
    return redirect('student_dashboard')

@login_required
def dashboard_redirect(request):
    return home(request)

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
            incident.reporter = request.user
            incident.case_token = generate_token()
            incident.status = 'New'
            incident.sentiment_score = calculate_advanced_sentiment(incident.description)
            
            is_critical = False
            if incident.sentiment_score <= -0.5:
                is_critical = True
                incident.is_emergency = True
                incident.internal_notes = "SYSTEM ALERT: Distress detected. Prioritized for review."
            
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
    
    status_filter = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    
    incidents = Incident.objects.all().annotate(
        priority_score=Case(
            When(Q(is_emergency=True) & ~Q(status='Resolved'), then=Value(3)),
            When(status='New', then=Value(2)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('-priority_score', '-reported_at')
    
    if status_filter == 'critical':
        incidents = incidents.filter(Q(is_emergency=True) | Q(sentiment_score__lte=-0.7))
    elif status_filter == 'pending':
        incidents = incidents.filter(status='New')
        
    if search_query:
        clean_query = search_query.lstrip('#')
        incidents = incidents.filter(
            Q(case_token__icontains=clean_query) | 
            Q(reporter__username__icontains=search_query) |
            Q(title__icontains=search_query)
        )
        
    return render(request, 'core/counsellor_dashboard.html', {
        'incidents': incidents, 
        'active_filter': status_filter, 
        'search_query': search_query
    })

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()
    emergency_only = request.GET.get('emergency')
    
    all_reports = Incident.objects.all().annotate(
        priority_score=Case(
            When(Q(is_emergency=True) & ~Q(status='Resolved'), then=Value(3)),
            When(status='New', then=Value(2)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('-priority_score', '-reported_at')
    
    if status_filter != 'all':
        all_reports = all_reports.filter(status=status_filter)
    
    if emergency_only == 'true':
        all_reports = all_reports.filter(is_emergency=True)
        
    if search_query:
        clean_token = search_query.lstrip('#')
        all_reports = all_reports.filter(
            Q(case_token__icontains=clean_token) |
            Q(description__icontains=search_query) |
            Q(reporter__username__icontains=search_query)
        )

    stats_qs = Incident.objects.all()
    raw_status = stats_qs.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in raw_status}
    
    formatted_status_counts = {
        'New': status_counts.get('New', 0),
        'Review': status_counts.get('Under Review', 0),
        'Action': status_counts.get('Action Taken', 0),
        'Resolved': status_counts.get('Resolved', 0),
    }

    context = {
        'incidents': all_reports,
        'staff_members': User.objects.filter(role__in=['counsellor', 'security']),
        'students': User.objects.filter(role='student'),
        'student_count': User.objects.filter(role='student').count(),
        'counsellor_count': User.objects.filter(role__in=['counsellor', 'security']).count(),
        'total_reports': stats_qs.count(),
        'avg_sentiment': stats_qs.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0,
        'status_counts': formatted_status_counts,
        'distressed_count': stats_qs.filter(sentiment_score__lte=-0.2).count(),
        'stable_count': stats_qs.filter(sentiment_score__gte=-0.2).count(),
        'search_query': search_query,
        'current_status': status_filter,
    }
    return render(request, 'core/admin_dashboard.html', context)


# --- 6. CHAT & DETAILS ---

@login_required
def view_incident(request, incident_id):
    """Staff View: For Counsellors/Security to update status and chat."""
    incident = get_object_or_404(Incident, id=incident_id)
    
    # 1. Permission Gate: Redirect students to their own chat
    if request.user.role not in ['counsellor', 'security', 'admin'] and not request.user.is_superuser:
        return redirect('chat_view', incident_id=incident.id)

    if request.method == 'POST':
        # LOGIC A: Handle Case Management (Always allowed for staff)
        if 'status' in request.POST:
            new_status = request.POST.get('status')
            incident.status = new_status
            incident.internal_notes = request.POST.get('internal_notes', '')
            
            if new_status == 'Resolved':
                Message.objects.create(
                    incident=incident,
                    sender=request.user,
                    text="✅ CASE RESOLVED: The administration has officially marked this incident as resolved."
                )
            
            incident.save()
            messages.success(request, f"Case updated: {new_status}")
            return redirect('view_incident', incident_id=incident.id)

        # LOGIC B: Handle Chat Messages
        elif 'message' in request.POST or request.FILES.get('attachment'):
            # If the sender is the original reporter and the report is anonymous
            # and identity hasn't been revealed, prevent the reporter from sending messages.
            # Staff (counsellor/security/admin) are allowed to message regardless.
            if request.user == incident.reporter and incident.is_anonymous and not incident.is_identity_revealed:
                messages.error(request, "Privacy Guard: You must reveal your identity to send messages.")
            else:
                text = request.POST.get('message', '').strip()
                file = request.FILES.get('attachment')
                if text or file:
                    # Duplicate guard: avoid creating identical messages within a short window
                    recent_cutoff = timezone.now() - timedelta(seconds=5)
                    is_duplicate = False
                    if text:
                        is_duplicate = Message.objects.filter(
                            incident=incident,
                            sender=request.user,
                            text=text,
                            created_at__gte=recent_cutoff
                        ).exists()
                    if not is_duplicate:
                        attach_dup = _is_duplicate_attachment(incident, request.user, file)
                        if not attach_dup:
                            Message.objects.create(
                                incident=incident, 
                                sender=request.user, 
                                text=text,
                                attachment=file
                            )
            return redirect('view_incident', incident_id=incident.id)

    chat_messages = Message.objects.filter(incident=incident).order_by('created_at')
    return render(request, 'core/view_incident.html', {
        'incident': incident, 
        'messages': chat_messages
    })

@login_required
def chat_view(request, incident_id):
    """Student View: For reporters to chat with staff."""
    incident = get_object_or_404(Incident, id=incident_id, reporter=request.user)
    
    if incident.status == 'Resolved' and request.method == 'POST':
        messages.error(request, "This case is resolved and the chat is closed.")
        return redirect('chat_view', incident_id=incident.id)

    if request.method == 'POST':
        if incident.is_anonymous and not incident.is_identity_revealed:
            messages.error(request, "Privacy Guard: You must reveal your identity to send messages.")
        else:
            text = request.POST.get('message', '').strip()
            file = request.FILES.get('attachment')
            if text or file:
                # Duplicate guard for student posts as well
                recent_cutoff = timezone.now() - timedelta(seconds=5)
                is_duplicate = False
                if text:
                    is_duplicate = Message.objects.filter(
                        incident=incident,
                        sender=request.user,
                        text=text,
                        created_at__gte=recent_cutoff
                    ).exists()
                if not is_duplicate:
                    attach_dup = _is_duplicate_attachment(incident, request.user, file)
                    if not attach_dup:
                        Message.objects.create(
                            incident=incident, 
                            sender=request.user, 
                            text=text,
                            attachment=file
                        )
        return redirect('chat_view', incident_id=incident.id)

    chat_messages = Message.objects.filter(incident=incident).order_by('created_at')
    return render(request, 'core/chat.html', {'incident': incident, 'messages': chat_messages})


@login_required
def reveal_identity(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id, reporter=request.user)
    incident.is_anonymous = False
    incident.is_identity_revealed = True
    incident.save()
    messages.success(request, "Identity revealed.")
    return redirect('chat_view', incident_id=incident.id)

@login_required
def export_incident_pdf(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    is_staff = request.user.role in ['admin', 'counsellor', 'security'] or request.user.is_superuser
    if not (is_staff or incident.reporter == request.user):
        return redirect('home')
        
    messages_list = Message.objects.filter(incident=incident).order_by('created_at')
    if pisa is None:
        return HttpResponse("PDF library not installed.", status=500)

    context = {'incident': incident, 'messages': messages_list, 'export_date': datetime.datetime.now()}
    template = get_template('core/incident_pdf_template.html')
    html = template.render(context)
    result = BytesIO()
    pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Case_{incident.case_token}.pdf"'
    return response

def resources_view(request):
    return render(request, 'core/resources.html')


@login_required
def assign_incident(request, incident_id):
    """Assign the incident to the current staff user (simple internal note update)."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    incident = get_object_or_404(Incident, id=incident_id)
    # Only staff may assign
    if request.user.role not in ['counsellor', 'security'] and not request.user.is_superuser:
        return HttpResponseForbidden('Forbidden')

    note = f"Assigned to {request.user.username} on {datetime.datetime.now().isoformat()}"
    incident.internal_notes = (incident.internal_notes or '') + '\n' + note
    incident.save()
    messages.success(request, f"Assigned to {request.user.username}")
    return HttpResponse(status=200)


@login_required
def resolve_incident(request, incident_id):
    """Mark an incident as resolved (staff only)."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    incident = get_object_or_404(Incident, id=incident_id)
    if request.user.role not in ['counsellor', 'security', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden('Forbidden')

    incident.status = 'Resolved'
    incident.save()
    Message.objects.create(
        incident=incident,
        sender=request.user,
        text="✅ CASE RESOLVED: Marked resolved via quick action."
    )
    messages.success(request, 'Case resolved')
    return HttpResponse(status=200)

@login_required
def admin_chat_view(request, incident_id):
    """Compliance view for Admins only."""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden: admin access only")
        
    incident = get_object_or_404(Incident, id=incident_id)
    
    if request.method == 'POST':
        text = request.POST.get('message', '')
        file = request.FILES.get('attachment')
        if text or file:
            attach_dup = _is_duplicate_attachment(incident, request.user, file)
            if not attach_dup:
                Message.objects.create(
                    incident=incident, 
                    sender=request.user, 
                    text=text,
                    attachment=file
                )
        return redirect('admin_chat_view', incident_id=incident.id)

    chat_messages = Message.objects.filter(incident=incident).order_by('created_at')
    return render(request, 'core/admin_chat_view.html', {
        'incident': incident, 
        'messages': chat_messages
    })