from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register"),
    path("cart/", views.cart, name="cart"),
    path("logout/", views.logout_user, name="logout"),
    path("user/<str:username>/", views.home_user, name="home_user")
]