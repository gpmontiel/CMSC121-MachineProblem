from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from . models import *
from . forms import CreateUserForm

# Create your views here.
def home(request):
    context = {}
    return render(request, "home.html", context)

@login_required (login_url="login")
def home_user(request, username):
    context = {
        "username" : username
    }
    return render(request, "home_user.html", context)

@login_required (login_url="login")
def cart(request):
    context = {}
    return render(request, "cart.html", context)

def login_user(request):
    if request.user.is_authenticated:
        return redirect("home_user", username=request.user.username)
    else:
        if request.method=="POST":
            username = request.POST.get("username")
            password = request.POST.get("password")
            if not username or not password:
                messages.error(request, "Please provide both username and password")
                return render(request, "login.html", {})
            try:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect("home_user", username=user.username)
                else:
                    messages.info(request, "Username or password is incorrect")
            except User.DoesNotExist:
                messages.info(request, "No account with this username exists")
            except Exception as e:
                messages.error(request, f"Login error: {str(e)}")

        context = {}
        return render(request, "login.html", context)
    
def register_user(request):
    if request.user.is_authenticated:
        return redirect('login')
    else:
        form = CreateUserForm
        if request.method == "POST":
            form = CreateUserForm(request.POST)
            if form.is_valid():
                try:
                    form.save()
                    username = form.cleaned_data.get("username")
                    messages.success(request, "Account created succesfully for " + username)
                    return redirect("login")
                except Exception as e:
                    messages.error(request, "Error creating account: {str(e)}")
        else:
            pass
    context = {"form": form}
    return render(request, "register.html", context)

def logout_user(request):
    try:
        logout(request)
        return redirect('login')
    except Exception as e:
        print(f"Logout error: {e}")
        messages.error(request, "Error during logout. Please try again.")
        return redirect('home')


