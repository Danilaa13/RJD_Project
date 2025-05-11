import json
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt # Временно для теста, лучше использовать CSRF токен!
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone

from users.models import UserRole
from .models import RepairRequest, CustomUser, RequestStatus


def welcome_screen(request):

    # if request.user.is_authenticated:
    #     if request.user.role == UserRole.DISPATCHER:
    #         return redirect('dispatcher_panel')
    #     elif request.user.role == UserRole.PEM:
    #         return redirect('pem_panel')

    return render(request, 'main/index.html')



# View для сохранения заявки через AJAX
# @csrf_exempt # Временно отключаем CSRF для простоты. НЕ ДЕЛАЙТЕ ТАК В PRODUCTION! Используйте токен.
@csrf_protect
@require_POST # Этот view должен принимать только POST запросы
def save_request_view(request):
    try:
        # Получаем JSON данные из тела запроса
        data = json.loads(request.body)

        # Извлекаем необходимые данные из тела запроса, которые приходят с ФРОНТЕНДА
        # Данные о рейсе, выбранный адресат (ПЭМ/ПДК) и данные о неисправности приходят с формы Проводника/ПЭМ
        path = data.get('path', [])
        code = data.get('code')
        target_role = data.get('targetRole')  # Получаем выбранного адресата

        # Данные пользователя, которые были собраны на фронтенде (ФИО, Табель, Город, Дата отправления, Поезд, Вагон)
        # ВАЖНО: ЭТИ ДАННЫЕ НУЖНЫ В ОСНОВНОМ ДЛЯ ПЕРЕДАЧИ, НО КТО СОЗДАЛ ЗАЯВКУ - БЕРЕТСЯ ИЗ request.user
        user_data_from_frontend = data.get('userData', {})

        departure_city = user_data_from_frontend.get('departureCity')
        departure_date_str = user_data_from_frontend.get('departureDate')  # Получаем как строку
        train = user_data_from_frontend.get('train')
        wagon = user_data_from_frontend.get('wagon')

        # Получаем данные о создателе заявки из request.user (ТРЕБУЕТ @login_required!)
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Пользователь не авторизован."}, status=401)

        creator_user = request.user  # Получаем объект авторизованного пользователя
        creator_role = creator_user.role  # Его текущая роль
        creator_tabel = creator_user.tabel  # Его табельный номер
        creator_fio = creator_user.fio  # Его ФИО

        # Проверяем наличие ОБЯЗАТЕЛЬНЫХ данных для ЛЮБОЙ заявки
        if not all([path, code, target_role]):  # Проверяем путь, код и АДРЕСАТА
            missing_fields = []
            if not path: missing_fields.append('path')
            if not code: missing_fields.append('code')
            if not target_role: missing_fields.append('targetRole')
            return JsonResponse({"status": "error",
                                 "message": f"Неполные основные данные заявки. Отсутствуют поля: {', '.join(missing_fields)}"},
                                status=400)

        # Проверяем наличие ОБЯЗАТЕЛЬНЫХ полей рейса для конкретных ролей (Проводник, ПЭМ)
        departure_date_obj = None
        # Проверяем роль СОЗДАТЕЛЯ (creator_role), а не role из user_data_from_frontend
        if creator_role in [UserRole.CONDUCTOR, UserRole.PEM]:  # Используйте константы из UserRole
            if not all([departure_city, departure_date_str, train, wagon]):
                return JsonResponse({"status": "error",
                                     "message": f"Для роли '{creator_role}' обязательны город отправления, дата отправления, поезд и вагон."},
                                    status=400)
            # Валидация формата даты и преобразование в объект date
            try:
                # Используем departure_date_str, полученный с фронтенда
                departure_date_obj = datetime.strptime(departure_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse(
                    {"status": "error", "message": "Неверный формат даты отправления (ожидается ГГГГ-ММ-ДД)."},
                    status=400)
        else:
            # Для других ролей данные рейса не обязательны
            departure_city = None
            train = None
            wagon = None
            departure_date_obj = None  # Убедимся, что date_obj тоже None

        # Валидация формата пути и кода
        if not isinstance(path, list) or not isinstance(code,
                                                        str) or not code:  # Проверяем, что код - строка и не пустая
            return JsonResponse({"status": "error", "message": "Неверный формат пути или кода неисправности."},
                                status=400)

        # Определяем начальный статус заявки на основе выбранного адресата (target_role)
        initial_status = RequestStatus.PENDING  # По умолчанию
        if target_role == UserRole.PEM:  # Если адресована ПЭМ (нужно обогащение)
            initial_status = RequestStatus.PENDING  # Используем PENDING как "ожидает обогащения"
        elif target_role == UserRole.DISPATCHER:  # Если адресована Диспетчеру (значит, считается обогащенной)
            initial_status = RequestStatus.CLASSIFIED  # Используем CLASSIFIED как "обогащена, готова для Диспетчера"
        # Добавьте логику для других target_role, если они возможны (например, Ревизор)

        # Генерируем initial_description из последнего элемента пути, если path не пустой
        final_item_desc = path[-1] if path else 'Не указано'

        # Создаем новую запись заявки в базе данных
        # Используем creator_user для поля user
        # Используем creator_role, creator_tabel, creator_fio из request.user
        # Используем target_role, полученный из запроса
        # Используем initial_status, определенный выше
        # Используем departure_date_obj (объект Date)
        request_instance = RepairRequest.objects.create(
            user=creator_user,  # <-- Привязываем объект пользователя
            role=creator_role,  # <-- Роль создателя берем из request.user
            tabel=creator_tabel,  # <-- Табель создателя берем из request.user
            fio=creator_fio,  # <-- ФИО создателя берем из request.user

            departure_city=departure_city,
            departure_date=departure_date_obj,  # <-- Сохраняем как Date объект
            train=train,
            wagon=wagon,

            target_role=target_role,  # <-- СОХРАНЯЕМ ВЫБРАННОГО АДРЕСАТА

            path_info=json.dumps(path),  # <-- Сохраняем путь как JSON строку
            # fault_description: Это property в вашей модели, оно будет генерироваться
            initial_description=final_item_desc,  # <-- Сохраняем последний элемент пути как первичное описание

            repair_code=code,  # <-- Сохраняем код неисправности
            status=initial_status,  # <-- Устанавливаем статус в зависимости от адресата

            # created_at и updated_at заполнятся автоматически при использовании create()
        )

        # request_instance.save() # create() уже сохраняет, эта строка не нужна

        # Отправляем успешный ответ
        return JsonResponse({"status": "success", "message": f"Заявка {request_instance.pk} успешно принята.",
                             "request_id": request_instance.pk}, status=201)

    except json.JSONDecodeError:
        print("Ошибка: Неверный формат JSON в теле запроса.")
        return JsonResponse({"status": "error", "message": "Неверный формат данных заявки (ожидается JSON)."},
                            status=400)

    except Exception as e:
        # Ловим другие возможные ошибки (например, ошибки БД при сохранении)
        print(f"Неожиданная ошибка в save_request_view: {e}",
              exc_info=True)  # exc_info=True для полной трассировки в логах
        return JsonResponse(
            {"status": "error", "message": "Произошла внутренняя ошибка сервера при обработке запроса."},
            status=500)



@csrf_protect
@require_POST
def update_request_status_view(request, pk):


    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Пользователь не авторизован."}, status=401)


    if request.user.role not in [UserRole.DISPATCHER, UserRole.ADMIN]:
        return JsonResponse({"status": "error", "message": "Недостаточно прав для смены статуса."}, status=403)

    try:
        repair_request = get_object_or_404(RepairRequest, pk=pk)
        data = json.loads(request.body)
        new_status = data.get('status')

        print(f"--- Debug Update Status ---")
        print(f"Request PK: {pk}")
        print(f"Received new_status: '{new_status}' (Type: {type(new_status)})")
        valid_statuses = list(RequestStatus.values)
        print(f"Valid statuses from RequestStatus.values: {valid_statuses}")
        print(f"Is received status in valid statuses? {new_status in valid_statuses}")
        print(f"--- End Debug ---")

        if new_status not in valid_statuses:
            print("DEBUG: Invalid status condition met.")  # Добавим принт и здесь
            return JsonResponse({'status': 'error', 'message': 'Недопустимый статус.'}, status=400)

        valid_statuses = list(RequestStatus.values)
        if new_status not in valid_statuses:
            return JsonResponse({'status': 'error', 'message': 'Недопустимый статус.'}, status=400)

        repair_request.status = new_status
        # Возможно, обновить и другие поля (например, completed_at при статусе 'done')
        repair_request.save()

        return JsonResponse({'status': 'success', 'message': f'Статус заявки {pk} обновлен на {new_status}.'})

    except RepairRequest.DoesNotExist:
         return JsonResponse({'status': 'error', 'message': 'Заявка не найдена.'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON в запросе.'}, status=400)

    except Exception as e:
         print(f"Error updating status for request {pk}: {e}")
         return JsonResponse({'status': 'error', 'message': f'Внутренняя ошибка сервера: {e}'}, status=500)