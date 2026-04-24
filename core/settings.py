import os
from pathlib import Path

# Корень проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Безопасность
SECRET_KEY = 'django-insecure-90gbdsq2#!0kvp9orgl)v6$)hzx(_vy6^a%)@(4=4ucb+9x7zk'

DEBUG = True

# РАЗРЕШЕННЫЕ АДРЕСА: локальный IP и стандартные локалхосты
ALLOWED_HOSTS = ['192.168.0.111', '127.0.0.1', 'localhost']


# ПРИЛОЖЕНИЯ
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Модуль для красивого вывода чисел (разделители тысяч)
    'django.contrib.humanize',
    
    # Твое приложение
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# БАЗА ДАННЫХ
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ВАЛИДАЦИЯ ПАРОЛЕЙ
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ИНТЕРНАЦИОНАЛИЗАЦИЯ
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Almaty'

USE_I18N = True
USE_TZ = True

# НАСТРОЙКИ ФОРМАТИРОВАНИЯ ЧИСЕЛ (для цен с пробелами)
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = ' '
NUMBER_GROUPING = 3


# СТАТИКА
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# НАСТРОЙКИ АВТОРИЗАЦИИ
LOGIN_REDIRECT_URL = 'order_list'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'