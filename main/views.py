import json
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt # Временно для теста, лучше использовать CSRF токен!
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone

from .models import RepairRequest, CustomUser, RequestStatus


def welcome_screen(request):
    return render(request, 'main/index.html')



# View для сохранения заявки через AJAX
# @csrf_exempt # Временно отключаем CSRF для простоты. НЕ ДЕЛАЙТЕ ТАК В PRODUCTION! Используйте токен.
@csrf_protect
@require_POST # Этот view должен принимать только POST запросы
def save_request_view(request):
    try:
        # Получаем JSON данные из тела запроса
        data = json.loads(request.body)

        # Извлекаем необходимые данные
        user_data = data.get('userData', {}) # Получаем вложенный объект userData
        path = data.get('path', [])
        code = data.get('code')
        role = user_data.get('role') # Извлекаем role из userData
        tabel = user_data.get('tabel') # Извлекаем tabel из userData
        fio = user_data.get('fio') # Извлекаем fio из userData

        departure_city = user_data.get('departureCity')
        departure_date = user_data.get('departureDate')
        train = user_data.get('train')
        wagon = user_data.get('wagon')
        final_item = path[-1] if path else 'Не указано'  # Последний элемент пути


        # Проверяем наличие обязательных данных пользователя
        if not all([role, tabel, fio, path, code]):
            # Добавим более конкретное сообщение, что именно не хватает
            missing_fields = []
            if not role: missing_fields.append('role')
            if not tabel: missing_fields.append('tabel')
            if not fio: missing_fields.append('fio')
            if not path: missing_fields.append('path')
            if not code: missing_fields.append('code')
            return JsonResponse({"status": "error",
                                 "message": f"Неполные основные данные заявки. Отсутствуют поля: {', '.join(missing_fields)}"},
                                status=400)

            # Проверка наличия обязательных полей рейса для конкретных ролей
        departure_date_obj = None
        if role in ['Проводник', 'ПЭМ']:

            if not all([departure_city, departure_date, train, wagon]):
                return JsonResponse({"status": "error",
                                     "message": f"Для роли '{role}' обязательны город отправления, дата отправления, поезд и вагон."},
                                    status=400)
            # Валидация формата даты
            try:
                departure_date_obj = datetime.strptime(departure_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse(
                    {"status": "error", "message": "Неверный формат даты отправления (ожидается ГГГГ-ММ-ДД)."},
                    status=400)
        else:
            # Для других ролей данные рейса не обязательны, убеждаемся, что они None
            departure_city = None
            train = None
            wagon = None

        if not isinstance(path, list) or not code:
            return JsonResponse({"status": "error", "message": "Неверный формат пути или кода неисправности."},
                                status=400)

        try:
            user_instance = None
            if tabel and role:
                try:
                    user_instance = CustomUser.objects.get(tabel=tabel, role=role)
                except CustomUser.DoesNotExist:
                    print(f"WARNING: Пользователь с табелем {tabel} и ролью {role} не найден в БД для привязки заявки.")

        # Создаем новую запись заявки
            request_instance = RepairRequest.objects.create(
                user=user_instance,
                role=role,
                tabel=tabel,
                fio=fio,
                departure_city=departure_city,
                departure_date=departure_date_obj,
                train=train,
                wagon=wagon,
                path_info=json.dumps(path),
                fault_description=final_item,
                repair_code=code,
                status=RequestStatus.PENDING
            )

            request_instance.save()

            # Отправляем успешный ответ
            return JsonResponse({"status": "success", "message": f"Заявка {request_instance.pk} успешно принята.",
                                 "request_id": request_instance.pk}, status=201)

        except Exception as e:
            print(f"Ошибка при сохранении заявки в БД: {e}")
            return JsonResponse({"status": "error", "message": "Произошла ошибка при сохранении заявки в базу данных."},
                                status=500)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Неверный формат JSON в теле запроса."}, status=400)

    except Exception as e:
        print(f"Неожиданная ошибка в save_repair_request_view: {e}")
        return JsonResponse({"status": "error", "message": "Произошла внутренняя ошибка сервера при обработке запроса."},
                            status=500)


def dispatcher_panel_view(request):
    # Получаем все заявки (или фильтруем по необходимости)
    # Для примера возьмем все, отсортированные по умолчанию (новые сверху)
    all_requests = RepairRequest.objects.all()

    # Подсчет статистики (простой пример)
    stats = {
        'total': all_requests.count(),
        'in_progress': all_requests.filter(status='assigned').count(),
        'done': all_requests.filter(status='done').count(),
        'urgent': all_requests.filter(status='urgent').count(),
        # Можно добавить расчет изменений % за день, но это сложнее
    }

    context = {
        'requests': all_requests,
        'stats': stats,
        'current_time_iso': timezone.now().isoformat() # Для JS таймеров
    }
    return render(request, 'dispatcher/dispatcher_panel.html', context) # Укажите путь к шаблону панели



# Пример View для обновления статуса (вызывается кнопками на панели)
# @csrf_exempt # Опять же, временно
@require_POST
def update_request_status_view(request, pk):
    try:
        repair_request = get_object_or_404(RepairRequest, pk=pk)
        data = json.loads(request.body)
        new_status = data.get('status')

        # Проверяем, допустим ли новый статус
        valid_statuses = [choice[0] for choice in RepairRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'status': 'error', 'message': 'Недопустимый статус.'}, status=400)

        repair_request.status = new_status
        # Возможно, обновить и другие поля (например, completed_at при статусе 'done')
        repair_request.save()

        return JsonResponse({'status': 'success', 'message': f'Статус заявки {pk} обновлен на {new_status}.'})

    except RepairRequest.DoesNotExist:
         return JsonResponse({'status': 'error', 'message': 'Заявка не найдена.'}, status=404)
    except Exception as e:
         print(f"Error updating status for request {pk}: {e}")
         return JsonResponse({'status': 'error', 'message': f'Внутренняя ошибка сервера: {e}'}, status=500)