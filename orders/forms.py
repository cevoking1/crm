from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem

class OrderForm(forms.ModelForm):
    """Форма для создания основной части заказа (шапки)"""
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

# Создаем набор форм для позиций внутри заказа
OrderItemFormSet = inlineformset_factory(
    Order, 
    OrderItem,
    # Добавили material_width в список полей
    fields=['product', 'material_width', 'width', 'height', 'quantity'],
    extra=3,        # Количество пустых строк для ввода
    can_delete=True, # Позволяет удалять позиции при редактировании
    widgets={
        'product': forms.Select(attrs={'class': 'm3-input py-2'}),
        'material_width': forms.Select(attrs={'class': 'm3-input py-2'}),
        'width': forms.NumberInput(attrs={'class': 'm3-input py-2', 'placeholder': 'Ширина (м)'}),
        'height': forms.NumberInput(attrs={'class': 'm3-input py-2', 'placeholder': 'Высота (м)'}),
        'quantity': forms.NumberInput(attrs={'class': 'm3-input py-2', 'min': '1'}),
    }
)