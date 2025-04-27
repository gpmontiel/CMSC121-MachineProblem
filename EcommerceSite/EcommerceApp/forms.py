from django import forms
from .models import *


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'style': 'resize: none;'}),
        }