import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from .models import Order, OrderItem, Material
from .forms import OrderForm, OrderItemFormSet, MaterialForm  # Убедитесь, что MaterialForm здесь есть

def send_telegram(message):
    """Вспомогательная функция для отправки уведомлений в Telegram"""
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={'chat_id': chat_id, 'text': message}, timeout=5)
    except Exception:
        pass

@login_required
def order_list(request):
    """Главный дашборд: список заказов и аналитика"""
    today = timezone.now().date()
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    orders = Order.objects.all().order_by('-created_at')

    if query:
        orders = orders.filter(Q(client_name__icontains=query))
    if status_filter:
        orders = orders.filter(status=status_filter)

    orders_today = Order.objects.filter(created_at__date=today)
    total_today = sum(o.total_amount for o in orders_today)
    count_in_progress = Order.objects.filter(status='in_progress').count()
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
    }
    return render(request, 'orders/order_list.html', context)

@login_required
@permission_required('orders.add_order', raise_exception=True)
def order_create(request):
    """Создание заказа"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            formset.instance = order
            formset.save()
            send_telegram(f"🆕 Создан заказ №{order.id}\nКлиент: {order.client_name}\nСумма: {order.total_amount} ₸")
            return redirect('order_list')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
    return render(request, 'orders/order_form.html', {'form': form, 'formset': formset})

@login_required
@permission_required('orders.change_order', raise_exception=True)
def order_update(request, pk):
    """Редактирование заказа"""
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    return render(request, 'orders/order_form.html', {
        'form': form, 
        'formset': formset, 
        'is_edit': True
    })

@login_required
def order_detail(request, pk):
    """Детали заказа"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def update_order_status(request, order_id, new_status):
    """Смена статуса и списание материала"""
    order = get_object_or_404(Order, id=order_id)
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
        if new_status == 'in_progress':
            for item in order.items.all():
                item.deduct_stock()
            send_telegram(f"🏗 Заказ №{order.id} ({order.client_name}) в работе.")
        if new_status == 'ready':
            send_telegram(f"✅ Заказ №{order.id} ГОТОВ!")
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))

@login_required
def mark_item_defect(request, item_id):
    """Пометка брака"""
    item = get_object_or_404(OrderItem, id=item_id)
    if not item.is_defective:
        item.is_defective = True
        item.is_deducted = False 
        item.deduct_stock()
        send_telegram(f"⚠ БРАК! Заказ №{item.order.id}: {item.product.name}")
    else:
        item.is_defective = False
    item.save()
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))

@login_required
def warehouse_list(request):
    """Список материалов на складе"""
    materials = Material.objects.all().order_by('total_stock')
    return render(request, 'orders/warehouse.html', {'materials': materials})

# ТО ЧТО ВЫ ЗАБЫЛИ ДОБАВИТЬ:
@login_required
@permission_required('orders.add_material', raise_exception=True)
def material_create(request):
    """Создание нового материала на сайте"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('warehouse')
    else:
        form = MaterialForm()
    return render(request, 'orders/material_form.html', {'form': form})