from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
import uuid, random, datetime

from .models import *
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
    this_month = datetime.datetime.now().month

    context = {
        'total_sales': Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'monthly_earnings': Order.objects.filter(created_at__month=this_month).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'total_orders': Order.objects.count(),
        'total_customers': Order.objects.values('user').distinct().count(),
        'total_products': Product.objects.count(),
    }

    return render(request, 'dashboard.html', context)

@login_required
def products_view(request):
    products = Product.objects.all().order_by('-created_at')
    paginator = Paginator(products, 5)

    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'seller-products.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            additional_images = request.FILES.getlist('additional_images')
            for image in additional_images:
                ProductImage.objects.create(product=product, image=image)

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
            additional_images = request.FILES.getlist('additional_images')
            for image in additional_images:
                ProductImage.objects.create(product=product, image=image)
            return redirect('seller-products')
    else:
        form = ProductForm(instance=product)

    additional_images = product.images.all()

    return render(request, 'modify-product.html', {'form': form,'additional_images': additional_images,'product': product})

@login_required
def delete_product_image(request, image_id):
    try:
        image = ProductImage.objects.get(id=image_id)
    except ProductImage.DoesNotExist:
        print("Image Not Found")

    product_id = image.product.id
    image.delete()

    return redirect('modify-product', product_id=product_id)

@login_required
def order_list(request):
    orders = Order.objects.all()
    paginator = Paginator(orders, 10)

    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'orders': page_object,  
        'order_count': orders.count(),
        'page_object': page_object
    }

    return render(request,'orders.html', context)

@login_required
def order_details(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print("Image Not Found")

    return render(request,'order-details.html', {'order': order})

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Completed', 'Cancelled']:
            order.status = new_status
            order.save()

    return redirect('order_details', order_id=order.id)

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
            user = form.save()
            AccountProfile.objects.create(user=user, user_type='buyer')
            return redirect('login')
        else:
            # Send form errors as messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'register.html', {'form': form})
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
    all_products = list(Product.objects.all())
    featured_products = random.sample(all_products, min(4, len(all_products))) if all_products else []
    
    return render(request, 'home.html', {
        'featured_products': featured_products
    })

##----------- CART & CHECKOUT PAGE -----------##
def cart(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        if request.user.accountprofile.user_type != 'buyer':
            return redirect('login') 
    except User.accountprofile.RelatedObjectDoesNotExist:
        return redirect('login')
    
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
    }
    return render(request, 'cart.html', context)

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        if request.user.accountprofile.user_type != 'buyer':
            return redirect('login') 
    except User.accountprofile.RelatedObjectDoesNotExist:
        return redirect('login')

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
    return redirect('cart')

def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                return JsonResponse({'deleted': True})
        
        cart = cart_item.cart
        return JsonResponse({
            'quantity': cart_item.quantity,
            'subtotal': str(cart_item.get_subtotal()),
            'total': str(cart.get_total())
        })
    return redirect('cart')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart')

def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    total = cart.get_total()
    
    if request.method == 'POST':
        full_name = request.POST.get('fullName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zipCode')
        card_name = request.POST.get('cardName')
        card_number = request.POST.get('cardNumber')
        card_last_four = card_number[-4:] if card_number else "0000"
        
        if cart_items:
            order = Order.objects.create(
                user=request.user,
                order_number=str(uuid.uuid4().hex)[:10].upper(),
                full_name=full_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                total_price=total,
                card_last_four=card_last_four
            )
            
            for cart_item in cart_items:
                product = cart.item.product

                if product.stock < cart_item.quantity:
                    messages.error(request,f"Not enough stock for {product.name}.")
                    return redirect('cart')

                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )

                product.stock -= cart_item.quantity
                product.save()
            
            cart.items.all().delete()
            return redirect('thank_you', order_id=order.id)
        else:
            return redirect('cart')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'checkout.html', context)

def thank_you(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        order = None
        
    context = {
        'order': order,
    }
    return render(request, 'thank-you.html', context)

# HELPER FUNCTION
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
    categories = Category.objects.all()
    selected_category = request.GET.get('category')

    if selected_category:
        products = Product.objects.filter(category_id=selected_category)
    else:
        products = Product.objects.all()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    return render(request, 'products.html', {
        'products': page_object, 
        'categories': categories,
        'selected_category': selected_category,
        'product_count': products.count(),
        })

def view_product_details(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        print("Product Not Found")

    other_products = Product.objects.exclude(id=product_id)
    recommended_products = random.sample(list(other_products), min(4, other_products.count()))

    return render(request, 'product-details.html', {
        'product': product,
        'recommended_products': recommended_products,
    })