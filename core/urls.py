from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Стандартная админка Django
    path('admin/', admin.site.urls),
    
    # Подключаем все маршруты из приложения orders
    path('', include('orders.urls')),
]