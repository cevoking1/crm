from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Product(models.Model):
    """Каталог услуг: Баннеры, Оракал, Визитки и т.д."""
    TYPE_CHOICES = [
        ('per_m2', 'За квадратный метр'),
        ('per_unit', 'За штуку'),
    ]
    name = models.CharField(max_length=255, verbose_name="Название товара")
    calc_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Тип расчета")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    def __str__(self):
        return f"{self.name} ({self.get_calc_type_display()})"

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

class Order(models.Model):
    """Основной заказ: Шапка с клиентом и общим статусом"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('printed', 'Напечатан'),
        ('ready', 'Готов'),
        ('issued', 'Выдан'),
    ]
    client_name = models.CharField(max_length=255, verbose_name="Клиент")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Кто создал")

    def __str__(self):
        return f"Заказ №{self.id} - {self.client_name}"

    @property
    def total_amount(self):
        """Сумма всего заказа (без учета бракованных позиций)"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_area(self):
        """Общая площадь печати в заказе (для понимания расхода материала)"""
        return sum(item.area * item.quantity for item in self.items.all())

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class OrderItem(models.Model):
    """Детали заказа: Конкретные баннеры или наклейки"""
    MATERIAL_WIDTHS = [
        (1.20, '1.2 м'),
        (1.26, '1.26 м'),
        (1.37, '1.37 м'),
        (1.50, '1.5 м'),
        (1.60, '1.6 м'),
        (0.00, 'Штучно / Другое'),
    ]

    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    material_width = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        choices=MATERIAL_WIDTHS, 
        default=0.00, 
        verbose_name="Ширина материала"
    )
    width = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Ширина (м)")
    height = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Высота (м)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кол-во")
    
    # Логика брака
    is_defective = models.BooleanField(default=False, verbose_name="Брак")
    defect_comment = models.CharField(max_length=255, blank=True, null=True, verbose_name="Комментарий к браку")

    @property
    def area(self):
        """Площадь одной единицы: $S = \text{width} \times \text{height}$"""
        return self.width * self.height

    @property
    def total_price(self):
        """Расчет стоимости позиции"""
        if self.is_defective:
            return Decimal('0.00')
        
        if self.product.calc_type == 'per_m2':
            # Стоимость по площади: $Total = S \times \text{price} \times \text{quantity}$
            return self.area * self.product.price * self.quantity
        else:
            # Стоимость за единицу: $Total = \text{price} \times \text{quantity}$
            return self.product.price * self.quantity

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"