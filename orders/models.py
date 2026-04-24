from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class MaterialTemplate(models.Model):
    """Готовые шаблоны материалов (Пресеты для быстрого добавления)"""
    name = models.CharField(max_length=255, verbose_name="Название материала")
    material_type = models.CharField(
        max_length=10, 
        choices=[('roll', 'Рулон'), ('unit', 'Лист/Штука')], 
        default='roll', 
        verbose_name="Тип"
    )
    width = models.DecimalField(max_digits=10, decimal_places=3, default=0.00, verbose_name="Ширина (м)")
    height = models.DecimalField(max_digits=10, decimal_places=3, default=0.00, verbose_name="Высота (м)")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена закупа")

    def __str__(self):
        return f"{self.name} ({self.width}x{self.height})"

    class Meta:
        verbose_name = "Шаблон материала"
        verbose_name_plural = "Шаблоны материалов"


class Material(models.Model):
    """Склад: текущие остатки рулонов и листовых товаров"""
    TYPE_CHOICES = [
        ('roll', 'Рулон (погонные метры)'),
        ('unit', 'Лист/Штука'),
    ]
    name = models.CharField(max_length=255, verbose_name="Название материала")
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='roll', verbose_name="Тип")
    width = models.DecimalField(max_digits=10, decimal_places=3, default=0.00, verbose_name="Ширина (м)")
    height = models.DecimalField(max_digits=10, decimal_places=3, default=0.00, verbose_name="Высота (м)")
    total_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Остаток")
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, verbose_name="Критический остаток")
    
    # ФИНАНСЫ: Цена закупа за 1 п.м. или 1 шт.
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена закупа")

    def __str__(self):
        unit = "м" if self.material_type == 'roll' else "шт"
        return f"{self.name} — ост. {self.total_stock}{unit}"

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Склад материалов"


class MaterialLog(models.Model):
    """Мониторинг: история всех движений на складе"""
    ACTION_CHOICES = [
        ('in', 'Приход (пополнение)'),
        ('out', 'Расход (заказ)'),
        ('defect', 'Расход (брак/перепечатка)'),
        ('return', 'Возврат на склад'),
    ]
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='logs', verbose_name="Материал")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество")
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Тип действия")
    description = models.CharField(max_length=255, blank=True, verbose_name="Комментарий/Номер заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        verbose_name = "Лог движения материала"
        verbose_name_plural = "История склада"


class Product(models.Model):
    """Каталог услуг типографии"""
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
    """Основной заказ клиента"""
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
        """Выручка (сумма всего заказа)"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_profit(self):
        """ФИНАНСЫ: Чистая прибыль всего заказа (Выручка - Себестоимость материалов)"""
        return sum(item.profit for item in self.items.all())

    @property
    def total_area(self):
        """Общая площадь печати заказа"""
        return sum(item.area * item.quantity for item in self.items.all())

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    """Позиции внутри заказа"""
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
        """Площадь одной единицы"""
        return self.width * self.height

    @property
    def consumption(self):
        """Расчет расхода материала (п.м. для рулонов, шт для товаров)"""
        if not self.material: return Decimal('0.00')
        # Для рулонов списываем высоту (погонные метры), для штук — количество
        return self.height * self.quantity if self.material.material_type == 'roll' else Decimal(self.quantity)

    @property
    def total_price(self):
        """Сумма продажи позиции (0 если брак)"""
        if self.is_defective:
            return Decimal('0.00')
        if self.product.calc_type == 'per_m2':
            return self.area * self.product.price * self.quantity
        return self.product.price * self.quantity

    @property
    def cost(self):
        """Себестоимость материала для этой позиции"""
        if not self.material: return Decimal('0.00')
        return self.consumption * self.material.purchase_price

    @property
    def profit(self):
        """Чистая прибыль по позиции"""
        return self.total_price - self.cost

    def deduct_stock(self, is_defect_retry=False):
        """Списание материала с записью в лог"""
        if self.material and not self.is_deducted:
            needed = self.consumption
            if self.material.total_stock >= needed:
                self.material.total_stock -= needed
                self.material.save()
                self.is_deducted = True
                self.save()
                
                # Фиксируем списание в истории
                MaterialLog.objects.create(
                    material=self.material,
                    quantity=needed,
                    action_type='defect' if is_defect_retry else 'out',
                    description=f"Заказ №{self.order.id} ({self.product.name})"
                )
                return True, "Успешно списано"
            return False, f"Недостаточно {self.material.name} (требуется {needed})"
        return True, "Пропуск (уже списано или нет материала)"

    def return_stock(self):
        """Возврат материала на склад с записью в лог"""
        if self.material and self.is_deducted:
            amount = self.consumption
            self.material.total_stock += amount
            self.material.save()
            self.is_deducted = False
            self.save()
            
            MaterialLog.objects.create(
                material=self.material,
                quantity=amount,
                action_type='return',
                description=f"Возврат по заказу №{self.order.id}"
            )
            return True
        return False

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"