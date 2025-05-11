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

from dispatcher.views import get_latest_requests_view, delete_request_view
from electromechanic.views import pem_panel_view, get_pem_requests_view, classify_request_view
from main.views import welcome_screen, save_request_view, update_request_status_view
from users.views import register_view, login_view, logout_view, check_auth_view
from dispatcher.views import dispatcher_panel_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # URL для отображения формы ввода заявки
    path('', welcome_screen, name='request_form'),

    # URL для AJAX-запроса сохранения заявки
    path('api/request/save/', save_request_view, name='save_request_api'),

    # URL для отображения диспетчерской панели
    path('dispatcher/', dispatcher_panel_view, name='dispatcher_panel'),

    # Доп. URL для обновления статуса заявки (пример)
    path('api/request/<int:pk>/update_status/', update_request_status_view, name='update_request_status_api'),
    path('api/request/<int:pk>/delete/', delete_request_view, name='delete_request'),
    path('api/requests/latest/', get_latest_requests_view, name='api_get_latest_requests'),

    path('api/register/', register_view, name='api_register'),
    path('api/login/', login_view, name='api_login'),
    path('api/logout/', logout_view, name='api_logout'),
    path('api/check_auth/', check_auth_view, name='api_check_auth'),

# Страница панели ПЭМ
    path('pem-panel/', pem_panel_view, name='pem_panel'),
    path('api/requests/pem/', get_pem_requests_view, name='get_pem_requests'),
    path('api/request/<int:pk>/classify/', classify_request_view, name='classify_request'),
]


