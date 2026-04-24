from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from .models import Order, OrderItem
from .forms import OrderForm, OrderItemFormSet

@login_required
def order_list(request):
    """Главный дашборд: доступен всем сотрудникам"""
    today = timezone.now().date()
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    orders = Order.objects.all().order_by('-created_at')

    if query:
        orders = orders.filter(Q(client_name__icontains=query))
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Статистика для дашборда
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
    """Создание заказа: только для тех, у кого есть право 'add_order' (Дизайнеры)"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            formset.instance = order
            formset.save()
            return redirect('order_list')
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
    return render(request, 'orders/order_form.html', {'form': form, 'formset': formset})

@login_required
@permission_required('orders.change_order', raise_exception=True)
def order_update(request, pk):
    """Редактирование заказа: только для Дизайнеров (право 'change_order')"""
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
    """Детальное ТЗ: доступно всем сотрудникам для просмотра"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def update_order_status(request, order_id, new_status):
    """Смена статуса: доступна всем сотрудникам (Печатникам и Дизайнерам)"""
    order = get_object_or_404(Order, id=order_id)
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save()
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))

@login_required
def mark_item_defect(request, item_id):
    """Отметка брака: доступна всем сотрудникам для оперативного контроля"""
    item = get_object_or_404(OrderItem, id=item_id)
    item.is_defective = not item.is_defective
    item.save()
    return redirect(request.META.get('HTTP_REFERER', 'order_list'))