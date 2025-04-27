from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Product, Cart, CartItem 
from .forms import ProductForm

## SELLER SIDE
def seller_login(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'seller-login.html')

def seller_logout(request):
    logout(request)
    return redirect('seller-login')

@login_required
def dashboard(request):
    context = {
        'total_sales': 152267371,
        'total_customers': 47121,
        'total_products': 2312312,
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
    
    return render(request, 'add_product.html', {'form': form})

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

    return render(request, 'modify_product.html', {'form': form})

## BUYER SIDE
def login_user(request):
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


# Make sure you have at least one product in your database
@login_required
def add_test_product(request):
    """Temporary view to add a test product to cart"""
    if Product.objects.exists():
        product = Product.objects.first()
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
    else:
        messages.error(request, "No products found in database!")
        
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
def get_or_create_cart(request):
    """Get existing cart or create a new one"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    return cart

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
    product = Product.objects.get(id=product_id)
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect('cart')

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = CartItem.objects.get(id=item_id)
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return redirect('cart')
        
        cart_item.save()
    
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('cart') 