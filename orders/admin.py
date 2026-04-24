from django.contrib import admin
from .models import Product, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'calc_type', 'price')
    list_filter = ('calc_type',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1 # Сколько пустых строк для позиций выводить сразу
    fields = ('product', 'width', 'height', 'quantity', 'is_defective', 'get_item_total')
    readonly_fields = ('get_item_total',)

    def get_item_total(self, obj):
        return f"{obj.total_price} тг." if obj.id else "-"
    get_item_total.short_description = "Сумма позиции"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'status', 'get_total', 'created_at', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('client_name',)
    inlines = [OrderItemInline] # Добавляем позиции прямо в заказ

    def get_total(self, obj):
        return f"{obj.total_amount} тг."
    get_total.short_description = "Итоговая сумма"

    def save_model(self, request, obj, form, change):
        if not obj.pk: # Если заказ только создается
            obj.created_by = request.user
        super().save_model(request, obj, form, change)