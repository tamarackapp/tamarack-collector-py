from django.shortcuts import render
from django.contrib.auth.models import User

# Create your views here.

def index(request):
    users = User.objects.all()
    return render(request, 'index.html', { 'users': users })

def about(request):
    return render(request, 'about.html')
