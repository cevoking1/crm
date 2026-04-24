from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client_name']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя клиента или компания'}),
        }

# Создаем связку: один Заказ — много Позиций
OrderItemFormSet = inlineformset_factory(
    Order, OrderItem,
    fields=['product', 'width', 'height', 'quantity'],
    extra=3, # Сколько пустых строк для товаров показать сразу
    can_delete=False,
    widgets={
        'product': forms.Select(attrs={'class': 'form-select'}),
        'width': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ширина'}),
        'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Высота'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)