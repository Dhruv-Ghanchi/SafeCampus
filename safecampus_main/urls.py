from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- Auth & Routing ---
    path('', views.home, name='root'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),
    
    # Central router for the "Dashboard" link in the Navbar
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # --- Student Features ---
    # FIXED: This now matches the restored function in views.py
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('report/', views.report_incident, name='report_incident'),
    
    # Centralized Chat View for Students (Matches your chat.html logic)
    path('my-case/<int:incident_id>/chat/', views.chat_view, name='chat_view'),
    
    # Logic to reveal identity in anonymous cases
    path('reveal/<int:incident_id>/', views.reveal_identity, name='reveal_identity'),
    
    # SOS Emergency Path (Used by the JavaScript voice recorder)
    path('handle-sos/', views.handle_sos_recording, name='handle_sos_recording'),
    
    # --- Staff/Counsellor Features ---
    path('counsellor/', views.counsellor_dashboard, name='counsellor_dashboard'),
    # Staff incident detail view for counsellors/security
    path('incident/<int:incident_id>/', views.view_incident, name='view_incident'),
    path('incident/<int:incident_id>/export-pdf/', views.export_incident_pdf, name='export_incident_pdf'),
    path('incident/<int:incident_id>/assign/', views.assign_incident, name='assign_incident'),
    path('incident/<int:incident_id>/resolve/', views.resolve_incident, name='resolve_incident'),
    
    # --- Admin & Audit Features ---
    path('admin-portal/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-chat/<int:incident_id>/', views.admin_chat_view, name='admin_chat_view'),
    
    # PDF Export (Synchronized with the 'Open PDF' buttons in your portal)
    path('incident/<int:incident_id>/export-pdf/', views.export_incident_pdf, name='export_incident_pdf'),
    
    # General Resources
    path('resources/', views.resources_view, name='resources'),
]

# Media Handling for Development (Crucial for Audio recordings and Chat attachments)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)