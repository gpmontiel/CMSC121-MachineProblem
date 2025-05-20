from django.contrib import admin
from .models import *

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ProductImage)
admin.site.register(AccountProfile)
admin.site.register(Order)
admin.site.register(OrderItem)