

import json
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET # Используем require_GET
from django.views.decorators.csrf import csrf_exempt # Для GET запросов часто не нужен, но можно оставить csrf_protect если сессия важна
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.core.serializers import serialize # Полезно для сериализации queryset

# Импортируйте вашу модель заявки и пользователя
from main.models import RepairRequest, RequestStatus
from main.models import CustomUser





@require_GET
def get_latest_requests_view(request):
    """
    Возвращает список заявок, созданных после определенного времени, в формате JSON.
    Принимает GET параметр 'latest_id'.
    """

    latest_id_str = request.GET.get('latest_id')
    latest_requests_qs = RepairRequest.objects.none()

    try:
        latest_id = int(latest_id_str or 0)  # Преобразуем в число, если есть, иначе 0
    except (ValueError, TypeError):
        latest_id = 0  # Если параметр не число, считаем его 0

    if latest_id >= 0:  # Убедимся, что ID не отрицательный
        # Фильтруем заявки: ID должен быть БОЛЬШЕ (>) latest_id
        latest_requests_qs = RepairRequest.objects.filter(id__gt=latest_id).order_by(
            'id')  # Сортируем по ID (или created_at)
        # Вы можете добавить .select_related('user'), если часто обращаетесь к пользователю в цикле
    else:
        # Можно вернуть ошибку, если пришел некорректный ID, но безопаснее отдать пустой список
        pass  # latest_requests_qs уже пустой


    requests_list = []
    for req in latest_requests_qs:
        # Проверяем, что поле fault_description существует или используем property
        fault_desc = ""
        if hasattr(req, 'fault_description'):
            fault_desc = req.fault_description
        elif hasattr(req, 'path_info'):  # Пытаемся получить из path_info как fallback
            try:
                path_list = json.loads(req.path_info or '[]')
                if isinstance(path_list, list) and len(path_list) > 0:
                    fault_desc = str(path_list[-1])
            except:
                fault_desc = req.repair_code or "-"  # Fallback на код или прочерк

        requests_list.append({
            'id': req.id,
            'status': req.status,
            'status_display': req.get_status_display(),
            'deadline': req.deadline.isoformat() if req.deadline else None,
            'created_at': req.created_at.isoformat(),  # ВАЖНО: ISO формат для JS
            'role': req.role,
            'tabel': req.tabel,
            'fio': req.fio,
            'departure_city': req.departure_city,
            'departure_date': req.departure_date.isoformat() if req.departure_date else None,  # ВАЖНО: ISO формат
            'train': req.train,
            'wagon': req.wagon,
            'path_info': req.path_info,
            'fault_description': fault_desc,  # Используем полученное описание
            'repair_code': req.repair_code,
            'route': req.route,
            'location': req.location,
        })

    return JsonResponse({"status": "success", "requests": requests_list})
