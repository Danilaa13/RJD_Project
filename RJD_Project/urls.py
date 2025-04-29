"""
URL configuration for RJD_Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # URL для отображения формы ввода заявки
    path('', views.welcome_screen, name='request_form'),

    # URL для AJAX-запроса сохранения заявки
    path('api/request/save/', views.save_request_view, name='save_request_api'),

    # URL для отображения диспетчерской панели
    path('dispatcher/', views.dispatcher_panel_view, name='dispatcher_panel'),

    # Доп. URL для обновления статуса заявки (пример)
    path('api/request/<int:pk>/update_status/', views.update_request_status_view, name='update_request_status_api'),
]


