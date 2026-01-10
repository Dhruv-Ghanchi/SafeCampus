from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('', views.home, name='home'),
    
    # Student Paths
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('report/', views.report_incident, name='report_incident'),
    path('my-case/<int:incident_id>/', views.student_incident_detail, name='student_incident_detail'),
    path('reveal/<int:incident_id>/', views.reveal_identity, name='reveal_identity'),
    
    # SOS Emergency Path (New)
    path('handle-sos/', views.handle_sos_recording, name='handle_sos'),
    
    # Counsellor Paths
    path('counsellor/', views.counsellor_dashboard, name='counsellor_dashboard'),
    path('incident/<int:incident_id>/', views.view_incident, name='view_incident'),
    
    # Admin Paths
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-chat/<int:incident_id>/', views.admin_view_chat, name='admin_view_chat'),
    
    # Resources Path
    path('resources/', views.resources_view, name='resources'),
]

# CRITICAL: This allows Django to serve the audio recordings and evidence files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)