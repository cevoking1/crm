from django.contrib import admin
from .models import Product, Order, OrderItem, Material
from .models import Product, Order, OrderItem, Material, MaterialTemplate

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    """Управление складом материалов"""
    list_display = ('name', 'material_type', 'width', 'total_stock', 'min_stock')
    list_filter = ('material_type',)
    search_fields = ('name',)
    # Группировка полей для удобства
    fieldsets = (
        (None, {
            'fields': ('name', 'material_type')
        }),
        ('Параметры и остатки', {
            'fields': ('width', 'total_stock', 'min_stock'),
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Управление каталогом услуг"""
    list_display = ('name', 'calc_type', 'price', 'default_material')
    list_filter = ('calc_type',)
    search_fields = ('name',)

class OrderItemInline(admin.TabularInline):
    """Позиции заказа внутри страницы заказа"""
    model = OrderItem
    extra = 1
    # Добавлено поле material для выбора со склада прямо в админке
    fields = ('product', 'material', 'width', 'height', 'quantity', 'is_defective', 'get_item_total')
    readonly_fields = ('get_item_total',)

    def get_item_total(self, obj):
        return f"{obj.total_price} тг." if obj.id else "-"
    get_item_total.short_description = "Сумма позиции"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Управление заказами"""
    list_display = ('id', 'client_name', 'status', 'get_total', 'created_at', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('client_name',)
    inlines = [OrderItemInline]

    def get_total(self, obj):
        return f"{obj.total_amount} тг."
    get_total.short_description = "Итоговая сумма"

    def save_model(self, request, obj, form, change):
        """Автоматическое назначение менеджера при создании через админку"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(MaterialTemplate)
class MaterialTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'material_type', 'width', 'purchase_price')
    search_fields = ('name',)