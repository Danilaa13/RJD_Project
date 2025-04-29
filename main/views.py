import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # Временно для теста, лучше использовать CSRF токен!
from django.utils import timezone

from .models import RepairRequest


def welcome_screen(request):
    return render(request, 'main/index.html')



# View для сохранения заявки через AJAX
# @csrf_exempt # Временно отключаем CSRF для простоты. НЕ ДЕЛАЙТЕ ТАК В PRODUCTION! Используйте токен.
@require_POST # Этот view должен принимать только POST запросы
def save_request_view(request):
    try:
        # Получаем JSON данные из тела запроса
        data = json.loads(request.body)

        # Извлекаем необходимые данные
        user_data = data.get('userData', {})
        path_list = data.get('path', [])
        code = data.get('code')
        final_item = path_list[-1] if path_list else 'Не указано' # Последний элемент пути

        # Проверяем наличие обязательных данных
        if not all([user_data.get('fio'), user_data.get('tabel'), user_data.get('train'), user_data.get('wagon'), path_list, code]):
             return JsonResponse({'status': 'error', 'message': 'Не все данные предоставлены.'}, status=400)

        # Создаем объект заявки
        new_request = RepairRequest(
            employee_fio=user_data['fio'],
            employee_tabel=user_data['tabel'],
            train_number=user_data['train'],
            wagon_number=user_data['wagon'],
            category_path=' › '.join(path_list), # Соединяем путь в строку
            fault_description=final_item,
            classification_code=code,
            # status='new' # Статус по умолчанию 'new'
            # deadline будет вычислен в методе save() модели
        )
        new_request.save() # Сохраняем в базу данных

        # Отправляем успешный ответ
        return JsonResponse({'status': 'success', 'message': 'Заявка успешно создана!', 'request_id': new_request.id})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Ошибка декодирования JSON.'}, status=400)
    except Exception as e:
        # Логгирование ошибки здесь может быть полезно
        print(f"Error saving request: {e}") # Вывод в консоль для отладки
        return JsonResponse({'status': 'error', 'message': f'Внутренняя ошибка сервера: {e}'}, status=500)

# View для отображения диспетчерской панели
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