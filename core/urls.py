# reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/chat/<int:incident_id>/', views.admin_chat_view, name='admin_chat_view'),
]