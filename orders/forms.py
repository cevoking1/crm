from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem, Material, MaterialTemplate

# --- Форма заказа ---
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

# --- ПОЛНАЯ ФОРМА ДЛЯ МАТЕРИАЛОВ ---
class MaterialForm(forms.ModelForm):
    # Поле для выбора из готовых шаблонов (не сохраняется в БД напрямую)
    template = forms.ModelChoiceField(
        queryset=MaterialTemplate.objects.all(),
        required=False,
        label="Выбрать из готовых",
        widget=forms.Select(attrs={'class': 'm3-input', 'onchange': 'applyTemplate(this)'})
    )

    class Meta:
        model = Material
        # Добавлены все необходимые поля, включая высоту и цену закупа
        fields = ['template', 'name', 'material_type', 'width', 'height', 'total_stock', 'min_stock', 'purchase_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'm3-input', 'id': 'id_name'}),
            'material_type': forms.Select(attrs={'class': 'm3-input', 'id': 'id_type'}),
            'width': forms.NumberInput(attrs={'class': 'm3-input', 'id': 'id_width', 'step': '0.001'}),
            'height': forms.NumberInput(attrs={'class': 'm3-input', 'id': 'id_height', 'step': '0.001'}),
            'total_stock': forms.NumberInput(attrs={'class': 'm3-input', 'step': '0.01'}),
            'min_stock': forms.NumberInput(attrs={'class': 'm3-input', 'step': '0.01'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'm3-input', 'id': 'id_purchase_price', 'step': '0.01'}),
        }

# --- Формсет позиций заказа ---
OrderItemFormSet = inlineformset_factory(
    Order, 
    OrderItem,
    fields=['product', 'material', 'width', 'height', 'quantity'],
    extra=1,
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'm3-input py-2'}),
        'material': forms.Select(attrs={'class': 'm3-input py-2'}),
        'width': forms.NumberInput(attrs={'class': 'm3-input py-2', 'placeholder': 'Ширина (м)', 'step': '0.001'}),
        'height': forms.NumberInput(attrs={'class': 'm3-input py-2', 'placeholder': 'Высота (м)', 'step': '0.001'}),
        'quantity': forms.NumberInput(attrs={'class': 'm3-input py-2', 'min': '1'}),
    }
)