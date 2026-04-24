from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Material(models.Model):
    """Склад: рулоны (пог.м.) или штучный товар"""
    TYPE_CHOICES = [
        ('roll', 'Рулон (погонные метры)'),
        ('unit', 'Штучный товар'),
    ]
    name = models.CharField(max_length=255, verbose_name="Название материала")
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='roll', verbose_name="Тип")
    width = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Ширина рулона (м)")
    total_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Остаток (м/шт)")
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, verbose_name="Критический остаток")

    def __str__(self):
        unit = "м" if self.material_type == 'roll' else "шт"
        return f"{self.name} ({self.width}м) — ост. {self.total_stock}{unit}"

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Склад материалов"

class Product(models.Model):
    """Каталог услуг"""
    TYPE_CHOICES = [('per_m2', 'За квадратный метр'), ('per_unit', 'За штуку')]
    name = models.CharField(max_length=255, verbose_name="Название товара")
    calc_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Тип расчета")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    default_material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Материал по умолчанию")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

class Order(models.Model):
    """Основной заказ"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
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
        """Сумма всего заказа"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_area(self):
        """Общая площадь печати"""
        return sum(item.area * item.quantity for item in self.items.all())

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class OrderItem(models.Model):
    """Позиции заказа"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, verbose_name="Материал со склада")
    
    width = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Ширина (м)")
    height = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Высота (м)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кол-во")
    
    is_defective = models.BooleanField(default=False, verbose_name="Брак")
    is_deducted = models.BooleanField(default=False, verbose_name="Списано со склада")

    @property
    def area(self):
        return self.width * self.height

    @property
    def total_price(self):
        if self.is_defective:
            return Decimal('0.00')
        if self.product.calc_type == 'per_m2':
            return self.area * self.product.price * self.quantity
        return self.product.price * self.quantity

    def deduct_stock(self):
        """Списание материала при запуске в печать или перепечатке брака"""
        if self.material and not self.is_deducted:
            # Для рулонов списываем высоту (погонные метры), для штук — количество
            consumption = self.height * self.quantity if self.material.material_type == 'roll' else self.quantity
            if self.material.total_stock >= consumption:
                self.material.total_stock -= consumption
                self.material.save()
                self.is_deducted = True
                self.save()
                return True
        return False

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"