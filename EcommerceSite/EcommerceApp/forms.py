from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from . models import UserProfile
from django.contrib.auth.models import User

class CreateUserForm(UserCreationForm):
    username = forms.CharField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    birthday = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'placeholder': 'Birth Date',
            'class': 'form-control',
            'type': 'date',
            'format': 'yyyy-mm-dd',
        }),
        input_formats=['%Y-%m-%d'],
    )
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "birthday", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use")
        return username

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit=False)
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        base_username = user.username
        while User.objects.filter(username=user.username).exists():
            user.username = f"{base_username}{n}"
            n += 1
        if commit:
            user.save()
            profile = UserProfile(
                user=user,
                birthday=self.cleaned_data['birthday']
            )
            profile.save()
            
        return user

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'style': 'resize: none;'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock
