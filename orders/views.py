import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from .models import Order, OrderItem, Material, MaterialLog, Product
from .forms import OrderForm, OrderItemFormSet, MaterialForm

def send_telegram(message):
    """Отправка уведомлений в Telegram бота"""
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={'chat_id': chat_id, 'text': message}, timeout=5)
    except Exception:
        pass

@login_required
def order_list(request):
    """Главный экран: список заказов и выручка/прибыль за сегодня"""
    today = timezone.now().date()
    query = request.GET.get('q', '')
    
    orders = Order.objects.all().order_by('-created_at')
    if query:
        orders = orders.filter(Q(client_name__icontains=query))

    # Финансовая сводка за текущий день
    orders_today = Order.objects.filter(created_at__date=today)
    total_today = sum(o.total_amount for o in orders_today)
    profit_today = sum(o.total_profit for o in orders_today)
    
    context = {
        'orders': orders,
        'total_today': total_today,
        'profit_today': profit_today,
        'count_in_progress': Order.objects.filter(status='in_progress').count(),
        'count_defects': OrderItem.objects.filter(is_defective=True, order__created_at__date=today).count(),
        'query': query,
    }
    return render(request, 'orders/order_list.html', context)

@login_required
@permission_required('orders.add_order', raise_exception=True)
def order_create(request):
    """Создание нового заказа с позициями"""
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
    """Редактирование существующего заказа"""
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
    return render(request, 'orders/order_form.html', {'form': form, 'formset': formset, 'is_edit': True})

@login_required
def order_detail(request, pk):
    """Просмотр деталей заказа и ТЗ"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
@require_POST
def update_order_status(request, order_id, new_status):
    """Смена статуса заказа со списанием материалов при старте"""
    order = get_object_or_404(Order, id=order_id)
    if new_status in dict(Order.STATUS_CHOICES):
        # Логика списания со склада при запуске в работу
        if new_status == 'in_progress':
            errors = []
            for item in order.items.all():
                success, msg = item.deduct_stock()
                if not success:
                    errors.append(msg)
            
            if errors:
                # Если материалов не хватило — показываем страницу ошибки
                return render(request, 'orders/error_page.html', {'errors': errors, 'order': order})
            
            send_telegram(f"🏗 Заказ №{order.id} ({order.client_name}) запущен в работу.")
        
        elif new_status == 'ready':
            send_telegram(f"✅ Заказ №{order.id} ГОТОВ!")

        order.status = new_status
        order.save()
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))

@login_required
@require_POST
def mark_item_defect(request, item_id):
    """Пометка брака: списывает материал повторно или возвращает его при отмене"""
    item = get_object_or_404(OrderItem, id=item_id)
    if not item.is_defective:
        item.is_defective = True
        item.is_deducted = False # Сбрасываем флаг для повторного списания
        success, msg = item.deduct_stock(is_defect_retry=True)
        if success:
            send_telegram(f"⚠ БРАК! Заказ №{item.order.id}: {item.product.name}. Списан материал на перепечатку.")
    else:
        item.is_defective = False
        item.return_stock() # Возвращаем материал, если пометка брака была ошибочной
    item.save()
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))

@login_required
def warehouse_list(request):
    """Просмотр остатков на складе и логов последних движений"""
    materials = Material.objects.all().order_by('total_stock')
    logs = MaterialLog.objects.all().order_by('-created_at')[:10]
    return render(request, 'orders/warehouse.html', {'materials': materials, 'logs': logs})

@login_required
@permission_required('orders.add_material', raise_exception=True)
def material_create(request):
    """Добавление нового материала (поставка)"""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            # Записываем приход в историю склада
            MaterialLog.objects.create(
                material=material,
                quantity=material.total_stock,
                action_type='in',
                description="Первоначальное внесение / Приход товара"
            )
            return redirect('warehouse')
    else:
        form = MaterialForm()
    return render(request, 'orders/material_form.html', {'form': form})

@login_required
def finance_report(request):
    """Бизнес-аналитика: выручка, себестоимость и прибыль по услугам"""
    # Анализируем только выполненные заказы
    orders = Order.objects.filter(status__in=['ready', 'issued'])
    
    total_revenue = sum(o.total_amount for o in orders)
    total_profit = sum(o.total_profit for o in orders)
    total_cost = total_revenue - total_profit
    
    service_stats = {}
    for order in orders:
        for item in order.items.all():
            name = item.product.name
            if name not in service_stats:
                service_stats[name] = {'revenue': 0, 'profit': 0, 'quantity': 0}
            
            service_stats[name]['revenue'] += item.total_price
            service_stats[name]['profit'] += item.profit
            service_stats[name]['quantity'] += item.quantity

    # Расчет рентабельности каждой услуги для отчета
    for name in service_stats:
        rev = service_stats[name]['revenue']
        prof = service_stats[name]['profit']
        # Вычисляем процент маржи
        service_stats[name]['margin'] = (prof / rev * 100) if rev > 0 else 0

    context = {
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_cost': total_cost,
        'orders_count': orders.count(),
        'service_stats': service_stats,
    }
    return render(request, 'orders/finance_report.html', context)