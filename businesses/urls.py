# businesses/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # We'll add actual views later
    path('', views.dashboard, name='business_dashboard'),
]
