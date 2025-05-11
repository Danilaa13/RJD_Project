import json
from datetime import datetime, date
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt # Для GET запросов часто не нужен, но можно оставить csrf_protect если сессия важна
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.core.serializers import serialize

# Импортируйте вашу модель заявки и пользователя
from main.models import RepairRequest, RequestStatus
from main.models import CustomUser
from users.models import UserRole

DISPATCHER_VISIBLE_STATUSES = [
    RequestStatus.PENDING,
    RequestStatus.CLASSIFIED,
    RequestStatus.ASSIGNED,
    RequestStatus.IN_PROGRESS,
    RequestStatus.COMPLETED,
]




def dispatcher_panel_view(request):

    if not request.user.is_authenticated or request.user.role != UserRole.DISPATCHER:

        return redirect('request_form')

    status_filter = Q()
    for status in DISPATCHER_VISIBLE_STATUSES:
        status_filter |= Q(status=status)

    all_requests = RepairRequest.objects.filter(status_filter).order_by('-created_at')

    # Подсчет статистики (адаптируйте под нужные срезы, используя те же Q-фильтры)
    stats = {
        'total': all_requests.count(),
        'pending': all_requests.filter(status=RequestStatus.PENDING).count(),  # Сколько ожидают
        'classified': all_requests.filter(status=RequestStatus.CLASSIFIED).count(),  # Сколько классифицировано
        'in_progress': all_requests.filter(status=RequestStatus.IN_PROGRESS).count(),  # В работе
        'completed': all_requests.filter(status=RequestStatus.COMPLETED).count()
    }

    context = {
        'requests': all_requests,  # Передаем отфильтрованный список
        'stats': stats,
        'current_time_iso': timezone.now().isoformat()  # Для JS таймеров (если они используются для диспетчера)
    }

    return render(request, 'dispatcher/dispatcher_panel.html', context)



@require_GET
def get_latest_requests_view(request):
    """
    Возвращает список НОВЫХ заявок (ID > latest_id),
    которые должны быть видны Диспетчеру, в формате JSON.
    Принимает GET параметр 'latest_id'.
    """

    latest_id_str = request.GET.get('latest_id')
    latest_id = 0 # Начальное значение

    try:
        latest_id = int(latest_id_str or 0)
    except (ValueError, TypeError):
        # Если latest_id некорректен, можно просто начать с 0
        latest_id = 0


    status_filter = Q()
    for status in DISPATCHER_VISIBLE_STATUSES:
        status_filter |= Q(status=status)

    latest_requests_qs = RepairRequest.objects.filter(
        id__gt=latest_id
    ).filter(
        status_filter
    ).select_related('user', 'classified_by').order_by('id')

    requests_list = []
    for req in latest_requests_qs:
        # Сериализуем данные заявки для отправки на фронтенд
        # Убедитесь, что имена полей здесь соответствуют тому, что ожидает ваш dispatcher/script.js
        requests_list.append({
            'id': req.id,
            'status': req.status,
            'status_display': req.get_status_display(),
            # 'deadline': req.deadline.isoformat() if req.deadline else None, # <-- Убедитесь, что этой строки НЕТ
            'created_at': req.created_at.isoformat(),
            'role': req.role, # Роль создателя
            'tabel': req.tabel, # Табель создателя
            'fio': req.fio, # ФИО создателя
            'departure_city': req.departure_city,
            'departure_date': req.departure_date.isoformat() if req.departure_date else None,
            'train': req.train,
            'wagon': req.wagon,
            'path_info': req.path_info, # Передаем полный путь (JSON строка)
            'fault_description': req.fault_description, # Передаем обновленное описание (property)
            'repair_code': req.repair_code, # Передаем обновленный код
            'route': req.route,
            'location': req.location,
            # Добавляем информацию о классификации ПЭМом
            'classified_by_fio': req.classified_by.fio if req.classified_by else None, # ФИО классификатора
            'classified_at': req.classified_at.isoformat() if req.classified_at else None, # Время классификации
        })

    return JsonResponse({"status": "success", "requests": requests_list})

@csrf_protect
def delete_request_view(request, pk):

    if request.method != 'DELETE':
        return JsonResponse({"status": "error", "message": "Допускается только DELETE запрос."},
                            status=405)


    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Пользователь не авторизован."}, status=401)

    if request.user.role not in [UserRole.DISPATCHER, UserRole.ADMIN]:
        return JsonResponse({"status": "error", "message": "Недостаточно прав для удаления заявки."}, status=403)

    try:
        repair_request = get_object_or_404(RepairRequest, pk=pk)


        repair_request.delete()

        return JsonResponse({"status": "success", "message": f"Заявка {pk} успешно удалена."})

    except RepairRequest.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Заявка не найдена."}, status=404)
    except Exception as e:
        print(f"Ошибка при удалении заявки {pk}: {e}")
        return JsonResponse({"status": "error", "message": "Внутренняя ошибка сервера при удалении."}, status=500)


