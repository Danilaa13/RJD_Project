import json
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.db.models import Q

from main.models import RepairRequest, RequestStatus
from users.models import UserRole


# @login_required
def pem_panel_view(request):

    if not request.user.is_authenticated or request.user.role != UserRole.PEM:

        return redirect('welcome_screen')


    pem_requests = RepairRequest.objects.filter(
        target_role=UserRole.PEM,
        status=RequestStatus.PENDING  # Показываем только ожидающие классификации
        # Можно добавить другие статусы, если ПЭМ должен видеть и те, что "в работе" у него
    ).select_related('user')  # Оптимизация

    # Статистика для ПЭМ (пример)
    stats = {
        'total_assigned': pem_requests.count(),
        # Добавьте другие нужные счетчики
    }

    context = {
        'requests': pem_requests,
        'stats': stats,
        'current_time_iso': timezone.now().isoformat()
    }
    # Указываем ПРАВИЛЬНЫЙ путь к шаблону ПЭМ
    return render(request, 'electromechanic/electromechanic_panel.html', context)



@require_GET
def get_pem_requests_view(request):
    """ API для поллинга панели Электромеханика (ПЭМ). """
    latest_id_str = request.GET.get('latest_id')
    try:
        latest_id = int(latest_id_str or 0)
    except (ValueError, TypeError):
        latest_id = 0

    # Запрос для ПЭМ (те же фильтры, что и в pem_panel_view + фильтр по ID)
    latest_requests_qs = RepairRequest.objects.filter(
        id__gt=latest_id,
        target_role=UserRole.PEM,
        status=RequestStatus.PENDING
    ).select_related('user').order_by('id')

    # Сериализация (аналогично get_latest_requests_view)
    requests_list = []
    for req in latest_requests_qs:
        fault_desc = req.fault_description  # Используем property
        requests_list.append({
            'id': req.id, 'status': req.status, 'status_display': req.get_status_display(),
            'deadline': req.deadline.isoformat() if hasattr(req, 'deadline') and req.deadline else None,
            'created_at': req.created_at.isoformat(), 'role': req.role, 'tabel': req.tabel,
            'fio': req.fio, 'departure_city': req.departure_city,
            'departure_date': req.departure_date.isoformat() if req.departure_date else None,
            'train': req.train, 'wagon': req.wagon, 'path_info': req.path_info,
            'fault_description': fault_desc, 'repair_code': req.repair_code,
            'route': req.route, 'location': req.location,
            # Здесь не нужны данные о классификации, так как мы их только ожидаем
        })

    return JsonResponse({"status": "success", "requests": requests_list})


# --- НОВЫЙ View (API для Классификации Заявки ПЭМом) ---
@csrf_protect
@require_POST
def classify_request_view(request, pk):
    """ ПЭМ классифицирует заявку (уточняет путь и код). """


    if not request.user.is_authenticated or request.user.role != UserRole.PEM:
        return JsonResponse({"status": "error", "message": "Доступ запрещен."}, status=403)

    try:
        # Находим заявку, адресованную ПЭМ и ожидающую
        repair_request = get_object_or_404(RepairRequest, pk=pk, target_role=UserRole.PEM, status=RequestStatus.PENDING)
    except RepairRequest.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Заявка не найдена или уже обработана."}, status=404)

    try:
        data = json.loads(request.body)
        new_path = data.get('path')
        new_code = data.get('code')

        if not isinstance(new_path, list) or not new_code:
            return JsonResponse({"status": "error", "message": "Не передан новый путь или код неисправности."},
                                status=400)

        # Обновляем заявку
        repair_request.path_info = json.dumps(new_path)
        repair_request.repair_code = new_code
        repair_request.status = RequestStatus.CLASSIFIED  # Меняем статус на "Классифицирована"
        repair_request.classified_by = request.user  # Записываем, кто классифицировал
        repair_request.classified_at = timezone.now()  # Время классификации



        try:
            if isinstance(new_path, list) and len(new_path) > 0:
                repair_request.initial_description = str(new_path[-1])  # Обновляем описание
        except Exception:
            pass

        repair_request.save()

        return JsonResponse({"status": "success", "message": f"Заявка {pk} успешно классифицирована."})

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Неверный формат JSON."}, status=400)
    except Exception as e:
        print(f"Ошибка при классификации заявки {pk}: {e}")
        return JsonResponse({"status": "error", "message": "Внутренняя ошибка сервера при классификации."}, status=500)
