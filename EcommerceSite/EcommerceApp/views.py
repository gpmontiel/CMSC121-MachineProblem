from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from . models import *
# from . forms import CreateUserForm

# Create your views here.
def home(request):
    return render(request, "home.html")

def cart(request):
    return render(request, "cart.html")

def login(request):
    return render(request, "login.html")

def register(request):
    return render(request, "register.html")
    
