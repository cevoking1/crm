from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Order, OrderItem
from .forms import OrderForm, OrderItemFormSet

def order_list(request):
    """Главный дашборд: список заказов, поиск и аналитика за день"""
    today = timezone.now().date()
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    # Базовая выборка всех заказов
    orders = Order.objects.all().order_by('-created_at')

    # Логика поиска по имени клиента
    if query:
        orders = orders.filter(Q(client_name__icontains=query))
    
    # Фильтрация по статусу
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Расчет статистики для Google-карточек
    orders_today = Order.objects.filter(created_at__date=today)
    total_today = sum(o.total_amount for o in orders_today)
    
    # Счётчик заказов, которые сейчас у печатника
    count_in_progress = Order.objects.filter(status='in_progress').count()
    
    # Счётчик бракованных позиций за сегодня
    count_defects = OrderItem.objects.filter(
        is_defective=True, 
        order__created_at__date=today
    ).count()

    context = {
        'orders': orders,
        'total_today': total_today,
        'count_in_progress': count_in_progress,
        'count_defects': count_defects,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'orders/order_list.html', context)

def order_create(request):
    """Интерфейс создания заказа с вложенными позициями товаров"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            # Автоматическая привязка создателя, если пользователь авторизован
            if request.user.is_authenticated:
                order.created_by = request.user
            order.save()
            formset.instance = order
            formset.save()
            return redirect('order_list')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
    
    return render(request, 'orders/order_form.html', {
        'form': form, 
        'formset': formset
    })

def order_detail(request, pk):
    """Детальное техническое задание для печатника"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})

def update_order_status(request, order_id, new_status):
    """Быстрое обновление этапа производства"""
    order = get_object_or_404(Order, id=order_id)
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
    
    # Возврат на ту же страницу, где была нажата кнопка
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))

def mark_item_defect(request, item_id):
    """Переключение метки брака для конкретной позиции"""
    item = get_object_or_404(OrderItem, id=item_id)
    item.is_defective = not item.is_defective
    item.save()
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))