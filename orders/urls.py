from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Авторизация
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Заказы
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/edit/', views.order_update, name='order_edit'), # РЕДАКТИРОВАНИЕ
    path('status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_status'),
    path('item/<int:item_id>/defect/', views.mark_item_defect, name='mark_defect'),
]