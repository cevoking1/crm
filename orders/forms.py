from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem, Material

# --- Существующая форма OrderForm ---
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client_name']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'm3-input text-xl', 
                'placeholder': 'Имя клиента или название компании',
                'required': True
            }),
        }

# --- ФОРМА ДЛЯ МАТЕРИАЛОВ ---
class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'material_type', 'width', 'total_stock', 'min_stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'm3-input'}),
            'material_type': forms.Select(attrs={'class': 'm3-input'}),
            'width': forms.NumberInput(attrs={'class': 'm3-input'}),
            'total_stock': forms.NumberInput(attrs={'class': 'm3-input'}),
            'min_stock': forms.NumberInput(attrs={'class': 'm3-input'}),
        }

# --- Существующий OrderItemFormSet ---
OrderItemFormSet = inlineformset_factory(
    Order, 
    OrderItem,
    fields=['product', 'material', 'width', 'height', 'quantity'],
    extra=3,
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'm3-input py-2'}),
        'material': forms.Select(attrs={'class': 'm3-input py-2'}),
        'width': forms.NumberInput(attrs={'class': 'm3-input py-2', 'placeholder': 'Ширина (м)'}),
        'height': forms.NumberInput(attrs={'class': 'm3-input py-2', 'placeholder': 'Высота (м)'}),
        'quantity': forms.NumberInput(attrs={'class': 'm3-input py-2', 'min': '1'}),
    }
)