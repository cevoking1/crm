from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Авторизация: стандартные вьюхи Django для входа и выхода
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Заказы: основной рабочий поток
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/edit/', views.order_update, name='order_edit'),
    
    # Управление производством: смена статусов и пометка брака
    path('status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_status'),
    path('item/<int:item_id>/defect/', views.mark_item_defect, name='mark_defect'),
    
    # Склад: страница мониторинга остатков материалов
    path('warehouse/', views.warehouse_list, name='warehouse'),

    path('warehouse/', views.warehouse_list, name='warehouse'),
    path('warehouse/add/', views.material_create, name='material_add'),

    path('finance/', views.finance_report, name='finance_report'),
]