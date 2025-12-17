# businesses/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    """Business dashboard placeholder."""
    return render(request, 'businesses/dashboard.html')
