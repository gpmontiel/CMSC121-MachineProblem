from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import Product, Cart, CartItem
from .forms import ProductForm, RegisterForm

##------------------------------- SELLER SIDE -------------------------------##
def seller_login(request):
    error_message = ""

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            error_message = "Please enter username and password."
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                error_message = "Invalid username or password."

    return render(request, 'seller-login.html', {"error_message": error_message})

def seller_logout(request):
    logout(request)
    return redirect('seller-login')

@login_required
def dashboard(request):
    context = {
        'total_sales': 152267371,
        'total_customers': 47121,
        'total_products': Product.objects.count(),
    }

    return render(request, 'dashboard.html', context)

@login_required
def products_view(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'seller-products.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('seller-products') 
    else:
        form = ProductForm()
    
    return render(request, 'add-product.html', {'form': form})

@login_required
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        print("Product Not Found")

    product.delete()
    return redirect('seller-products')

@login_required
def modify_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        print("Product Not Found")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('seller-products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'modify-product.html', {'form': form})

##------------------------------- BUYER SIDE -------------------------------##
##----------- LOGIN/REGISTER PAGE -----------##
def login_user(request):
    if request.method=="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Please provide both username and password")
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Incorrect username or password.")
        return render(request, 'login.html', {'username_value': username})

    return render(request, "login.html")

def register_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            # Send form errors as messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('register')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def logout_user(request):
    try:
        logout(request)
    except Exception as e:
        messages.error(request, f"Logout error: {e}")
    return redirect('login')

##----------- HOME PAGE -----------##
def home(request):
    return render(request, 'home.html')

##----------- CART & CHECKOUT PAGE -----------##
@login_required
def cart(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
    }
    return render(request, 'cart.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"Added {product.name} to your cart!")
    return redirect('cart')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, "Item quantity increased.")
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                messages.success(request, "Item quantity decreased.")
            else:
                cart_item.delete()
                messages.success(request, "Item removed from cart.")
        return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    if request.method == 'POST':
        cart.items.all().delete()
        messages.success(request, "Order placed successfully!")
        return redirect('cart')
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
    }
    return render(request, 'checkout.html', context)

@login_required
def add_test_product(request):
    products = Product.objects.all()
    if products.exists():
        cart = get_or_create_cart(request)
        added_products = []
        for product in products:
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            added_products.append(product.name)
        messages.success(request, f"Added {len(added_products)} products to your cart!")
    else:
        messages.error(request, "No products found in database!")
    return redirect('cart')

# HELPER FUNCTION
@login_required
def get_or_create_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return cart

##----------- PRODUCTS PAGE -----------##
def search_view(request):
    query = request.GET.get('q')
    products = Product.objects.none()
    total_results = 0

    if query:
        products = Product.objects.filter(name__icontains=query)
        total_results = products.count()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'search.html', {
        'query': query,
        'total_results': total_results,
        'page_obj': page_obj,
    })

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products':products})

def view_product_details(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        print("Product Not Found")

    return render(request, 'product-details.html', {'product': product})