from django.db import models
from django.contrib.auth.models import User
from django.db.models import F, Sum, DecimalField

class AccountProfile(models.Model):
    USER_TYPE_CHOICES = (('buyer', 'Buyer'), ('seller', 'Seller'),)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='buyer')
    profile_image = models.ImageField(null=True, blank=True, upload_to='pfp/')

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField()
    features = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.name}"
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_total(self):
        total = self.items.aggregate(
        total=Sum(F('quantity') * F('product__price'), output_field=DecimalField())
        )['total']
        return total or 0
    
    def __str__(self):
        return f"Cart {self.id}"
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_add = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def get_subtotal(self):
        price = self.price_at_add if self.price_at_add is not None else self.product.price
        return price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
class Order(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Processing', 'Processing'),
                      ('Shipped', 'Shipped'), ('Delivered', 'Delivered'),
                      ('Completed', 'Completed'), ('Cancelled', 'Cancelled'),]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    card_last_four = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_subtotal(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"