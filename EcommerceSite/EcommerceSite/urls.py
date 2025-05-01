"""
URL configuration for EcommerceSite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from EcommerceApp import views

urlpatterns = [
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add-test-product/', views.add_test_product, name='add_test_product'),
    path('checkout/', views.checkout, name='checkout'),
    path('seller-login/', views.seller_login, name='seller-login'),
    path('seller-logout/', views.seller_logout, name='seller-logout'),
    path('seller-products/', views.products_view, name='seller-products'),
    path('products/add/', views.add_product, name='add-product'),
    path('products/delete/<int:product_id>', views.delete_product, name='delete-product'),
    path('products/modify/<int:product_id>', views.modify_product, name='modify-product'),
    path('login/', views.login_user, name='login'),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
