from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< Updated upstream
    path("", include("EcommerceApp.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
=======
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('seller-login/', views.seller_login, name='seller-login'),
    path('seller-logout/', views.seller_logout, name='seller-logout'),
    path('seller-products/', views.products_view, name='seller-products'),
    path('products/add/', views.add_product, name='add-product'),
    path('products/delete/<int:product_id>', views.delete_product, name='delete-product'),
    path('products/modify/<int:product_id>', views.modify_product, name='modify-product'),
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> Stashed changes
