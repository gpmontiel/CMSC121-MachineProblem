from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings
import uuid, random, datetime

from .models import *
from .forms import *

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
                if hasattr(user, 'accountprofile') and user.accountprofile.user_type == 'seller':
                    login(request, user)
                    request.session['is_seller'] = True
                    return redirect('dashboard')
                else:
                    error_message = "Access restricted to sellers only."
            else:
                error_message = "Invalid username or password."

    return render(request, 'seller/seller-login.html', {"error_message": error_message})

def seller_logout(request):
    logout(request)
    return redirect('seller-login')

@login_required
def dashboard(request):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    this_month = datetime.datetime.now().month

    top_products = (
        OrderItem.objects
        .values('product__id', 'product__name', 'product__image', 'product__price', 'product__stock')
        .annotate(total_ordered=Sum('quantity'))
        .order_by('-total_ordered')[:5]
    )

    context = {
        'total_sales': Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'monthly_earnings': Order.objects.filter(created_at__month=this_month).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'total_orders': Order.objects.count(),
        'total_customers': Order.objects.values('user').distinct().count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'top_products': top_products,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'seller/dashboard/dashboard.html', context)

@login_required
def products_view(request):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(products, 5)

    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'seller/products/seller-products.html', {'products': products})

@login_required
def add_product(request):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
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
    
    return render(request, 'seller/products/add-product.html', {'form': form})

@login_required
def delete_product(request, product_id):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        print("Product Not Found")

    product.is_active = False
    product.save()
    return redirect('seller-products')

@login_required
def modify_product(request, product_id):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    product = get_object_or_404(Product, id=product_id, is_active=True)

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

    return render(request, 'seller/products/modify-product.html', {
        'form': form,
        'additional_images': additional_images,
        'product': product
    })

@login_required
def delete_product_image(request, image_id):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    try:
        image = ProductImage.objects.get(id=image_id)
    except ProductImage.DoesNotExist:
        print("Image Not Found")

    product_id = image.product.id
    image.delete()

    return redirect('modify-product', product_id=product_id)

@login_required
def order_list(request):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    current_status = request.GET.get('status')

    if current_status:
        orders = Order.objects.filter(status=current_status)
    else:
        orders = Order.objects.all()

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'orders': page_object,  
        'order_count': orders.count(),
        'page_object': page_object,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': current_status
    }

    return render(request,'seller/orders/orders.html', context)

@login_required
def order_details(request, order_id):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print("Order Not Found")

    return render(request,'seller/orders/order-details.html', {'order': order})

@login_required
def update_order_status(request, order_id):
    if not has_seller_access(request):
        return redirect('home')
    if not is_seller_logged(request):
        return redirect('seller-login')
    
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Completed', 'Cancelled']:
            order.status = new_status
            order.save()

    return redirect('order_details', order_id=order.id)

def has_seller_access(request):
    return (hasattr(request.user, 'accountprofile') and
            request.user.accountprofile.user_type == 'seller')

def is_seller_logged(request):
    return request.session.get('is_seller')

##------------------------------- BUYER SIDE -------------------------------##
##----------- LOGIN/REGISTER PAGE -----------##
def login_user(request):
    if request.user.is_authenticated:
        try:
            if request.user.accountprofile.user_type == 'buyer':
                return redirect('profile')
        except AccountProfile.DoesNotExist:
            return redirect('logout')
        
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
        return render(request, 'buyer/login-register/login.html', {'username_value': username})

    return render(request, "buyer/login-register/login.html")

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
            return render(request, 'buyer/login-register/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'buyer/login-register/register.html', {'form': form})

def logout_user(request):
    try:
        logout(request)
    except Exception as e:
        messages.error(request, f"Logout error: {e}")
    return redirect('login')

##----------- HOME PAGE -----------##
def home(request):
    all_products = list(Product.objects.filter(is_active=True, stock__gt=10))
    featured_products = random.sample(all_products, min(4, len(all_products))) if all_products else []
    
    return render(request, 'buyer/home-shop/home.html', {
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

    return render(request, 'buyer/cart/cart.html', context)

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
        defaults={'quantity': 1, 'price_at_add': product.price}
    )

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"{product.name} quantity updated in cart.")
        else:
            messages.warning(request, f"Maximum stock of {product.stock} reached for {product.name}.")
    else:
        messages.success(request, f"{product.name} added to cart.")

    return redirect('product_detail', product_id=product.id)

def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action = request.POST.get('action')

        if action == 'increase':
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                return JsonResponse({
                    'quantity': cart_item.quantity,
                    'max_stock': cart_item.product.stock,
                    'subtotal': float(cart_item.get_subtotal()),
                    'total': float(cart_item.cart.get_total()),
                    'message': f"Maximum stock of {cart_item.product.stock} reached for {cart_item.product.name}"
                })
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart = cart_item.cart
                cart_item.delete()
                return JsonResponse({
                    'deleted': True,
                    'total': float(cart.get_total())
                })
        
        cart = cart_item.cart
        subtotal = cart_item.get_subtotal()
        total = cart.get_total()

        return JsonResponse({
            'quantity': cart_item.quantity,
            'subtotal': float(subtotal),
            'total': float(total)
        })

    return redirect('cart')

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.error(request, f"{product_name} removed from your cart")
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    total = cart.get_total()

    inactive_items = [item.product.name for item in cart_items if not item.product.is_active]
    out_of_stock_items = [item.product.name for item in cart_items if item.product.stock <= 0]

    if inactive_items or out_of_stock_items:
        for name in inactive_items:
            messages.error(request, f"Sorry, '{name}' is no longer available. Please remove them before proceeding.")

        for name in out_of_stock_items:
            messages.error(request, f"Sorry, '{name}' is out of stock. Please remove it before proceeding.")
        return redirect('cart')
   
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

        validation_errors = []
        if not full_name:
            validation_errors.append('Full name is required')
        if not email:
            validation_errors.append('Email is required')
        if not phone:
            validation_errors.append('Phone number is required')
        elif not phone.isdigit() or len(phone) != 10:
            validation_errors.append('Please enter a valid 10-digit phone number')
        if not address:
            validation_errors.append('Address is required')
        if not city:
            validation_errors.append('City is required')
        if not state:
            validation_errors.append('State is required')
        if not zip_code:
            validation_errors.append('Zip code is required')
        elif not zip_code.isdigit() or len(zip_code) != 5:
            validation_errors.append('Please enter a valid 5-digit zip code')
        if not card_name:
            validation_errors.append('Name on card is required')
        if not card_number:
            validation_errors.append('Card number is required')
        elif not card_number.isdigit() or len(card_number) != 16:
            validation_errors.append('Please enter a valid 16-digit card number')
        
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return render(request, 'buyer/cart/checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total': total,
            })
        
        if not cart_items:
            messages.warning(request, 'Your cart is empty. Please add items before checking out.')
            return redirect('cart')

        try:
            card_last_four = card_number[-4:] if card_number else "0000"
            
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
            

            out_of_stock_items = []
            for cart_item in cart_items:
                product = cart_item.product
                if product.stock < cart_item.quantity:
                    out_of_stock_items.append(f"{product.name} (requested: {cart_item.quantity}, available: {product.stock})")
                    continue
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=cart_item.quantity,
                    price=product.price
                )
                

                product.stock -= cart_item.quantity
                product.save()
            

            if out_of_stock_items:
                order.delete()
                for item in out_of_stock_items:
                    messages.error(request, f"Not enough stock for {item}")
                return redirect('cart')
            
            cart.items.all().delete()
            messages.success(request, f"Order #{order.order_number} has been placed successfully!")
            return redirect('thank_you', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f"An error occurred while processing your order: {str(e)}")
            return render(request, 'buyer/cart/checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total': total,
            })
   
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'buyer/cart/checkout.html', context)

def thank_you(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, "Order not found or you don't have permission to view it.")
        order = None
        return redirect('home')
       
    context = {
        'order': order,
    }
    
    return render(request, 'buyer/cart/thank-you.html', context)

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        cart, created = Cart.objects.get_or_create(session_id=session_id, user=None)
    
    return cart

##----------- SEARCH PAGE -----------##
def search_view(request):
    query = request.GET.get('q')
    products = Product.objects.none()
    total_results = 0

    if query:
        products = Product.objects.filter(name__icontains=query, is_active=True)
        total_results = products.count()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'buyer/home-shop/search.html', {
        'query': query,
        'total_results': total_results,
        'page_obj': page_obj,
    })

##----------- PRODUCTS PAGE -----------##
def product_list(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')

    if selected_category:
        products = Product.objects.filter(category_id=selected_category, is_active=True)
    else:
        products = Product.objects.filter(is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    # Build cart quantities
    cart = get_or_create_cart(request)
    cart_quantities = {}
    for item in cart.items.all():
        cart_quantities[item.product.id] = item.quantity

    return render(request, 'buyer/products/products.html', {
        'products': page_object, 
        'categories': categories,
        'selected_category': selected_category,
        'product_count': products.count(),
        'cart_quantities': cart_quantities,
    })


def view_product_details(request, product_id):
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        print("Product Not Found")

    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        quantity_in_cart = cart_item.quantity
    except CartItem.DoesNotExist:
        quantity_in_cart = 0

    other_products = Product.objects.filter(is_active=True, stock__gt=10).exclude(id=product_id)
    recommended_products = random.sample(list(other_products), min(4, other_products.count()))

    return render(request, 'buyer/products/product-details.html', {
        'product': product,
        'recommended_products': recommended_products,
        'quantity_in_cart': quantity_in_cart,
    })

##----------- PROFILE PAGE -----------##
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        profile = request.user.accountprofile
        if profile.user_type != 'buyer':
            return redirect('login') 
    except User.accountprofile.RelatedObjectDoesNotExist:
        return redirect('login')
    
    orders = Order.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ProfilePicForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfilePicForm(instance=profile)
    
    return render(request, 'buyer/home-shop/profile.html', {'orders': orders, 'form': form, 'profile': profile})

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.status == 'Pending':
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        order.status = 'Cancelled'
        order.save()

    return redirect('profile')