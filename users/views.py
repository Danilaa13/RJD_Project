import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect # Для проверки CSRF токена
from django.contrib.auth import authenticate, login, logout # Импортируем функции аутентификации Django
from django.db import IntegrityError
from django.views.decorators.http import require_GET
from django.forms.models import model_to_dict # Для удобного преобразования модели в словарь

# Импортируем вашу кастомную модель пользователя
from .models import CustomUser, UserRole # Замените .models на ваш_app.models при необходимости

@csrf_protect # Проверяем CSRF токен
@require_POST # Принимаем только POST запросы
def register_view(request):
    """Обрабатывает запросы на регистрацию новых пользователей."""
    try:
        data = json.loads(request.body) # Читаем JSON из тела запроса
        role = data.get('role')
        tabel = data.get('tabel')
        fio = data.get('fio')
        password = data.get('password')

        # Базовая валидация входных данных
        if not all([role, tabel, fio, password]):
            return JsonResponse({"status": "error", "message": "Не все обязательные поля заполнены."}, status=400)

        # Проверка, что переданная роль существует
        if role not in UserRole.values:
             return JsonResponse({"status": "error", "message": f"Недопустимая роль: {role}"}, status=400)

        # Создание пользователя с использованием встроенного метода Django
        # create_user правильно хеширует пароль
        try:
            user = CustomUser.objects.create_user(
                username=tabel, # Можете использовать табельный как username, если удобно
                role=role,
                tabel=tabel, # Сохраняем табельный номер и в отдельном поле
                fio=fio,
                password=password,
                # Устанавливаем is_active=True по умолчанию для новых пользователей
                is_active=True
            )
            # Если используете username для чего-то другого, установите его явно
            # user.username = ...
            # user.save() # Сохраните, если меняли username после create_user

            return JsonResponse({"status": "success", "message": "Пользователь успешно зарегистрирован."})

        except IntegrityError:
            # Обработка ошибки уникальности (role, tabel)
            return JsonResponse({"status": "error", "message": f"Пользователь с табельным номером {tabel} и ролью {role} уже существует."}, status=409) # 409 Conflict
        except Exception as e:
            # Обработка других возможных ошибок при создании пользователя
            print(f"Ошибка при регистрации пользователя: {e}") # Логирование ошибки на сервере
            return JsonResponse({"status": "error", "message": "Произошла ошибка при регистрации."}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Неверный формат JSON."}, status=400)
    except Exception as e:
         print(f"Неожиданная ошибка в register_view: {e}")
         return JsonResponse({"status": "error", "message": "Произошла внутренняя ошибка сервера."}, status=500)


@csrf_protect # Проверяем CSRF токен
@require_POST # Принимаем только POST запросы
def login_view(request):
    """Обрабатывает запросы на авторизацию пользователей."""
    try:
        data = json.loads(request.body)
        role = data.get('role')
        tabel = data.get('tabel')
        password = data.get('password')

        if not all([role, tabel, password]):
            return JsonResponse({"status": "error", "message": "Не все обязательные поля заполнены."}, status=400)

        # Проверка, что переданная роль существует
        if role not in UserRole.values:
             return JsonResponse({"status": "error", "message": f"Недопустимая роль: {role}"}, status=400)

        # Поиск пользователя по табельному номеру и роли
        try:
            user = CustomUser.objects.get(tabel=tabel, role=role)
        except CustomUser.DoesNotExist:
            # Пользователь не найден с такой комбинацией табельного и роли
            return JsonResponse({"status": "error", "message": "Неверный табельный номер или роль."}, status=401) # 401 Unauthorized

        # Проверка пароля для найденного пользователя
        if user.check_password(password):
            # Пароль верен. Аутентифицируем пользователя в сессии Django
            # Это полезно, если вы планируете использовать сессии для последующих запросов
            login(request, user)

            # Формируем данные пользователя для отправки на фронтенд (без пароля!)
            user_data_for_frontend = {
                "role": user.role,
                "tabel": user.tabel,
                "fio": user.fio,
                # Не включайте пароль или хеш пароля здесь!
            }

            return JsonResponse({"status": "success", "message": "Авторизация успешна.", "user": user_data_for_frontend})
        else:
            # Пароль неверный
            return JsonResponse({"status": "error", "message": "Неверный пароль."}, status=401) # 401 Unauthorized

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Неверный формат JSON."}, status=400)
    except Exception as e:
        print(f"Неожиданная ошибка в login_view: {e}")
        # Может быть полезно логгировать тип ошибки для отладки
        # import traceback
        # traceback.print_exc()
        return JsonResponse({"status": "error", "message": "Произошла внутренняя ошибка сервера."}, status=500)

# Опционально: View для выхода из системы
@require_POST
def logout_view(request):
    """Обрабатывает запросы на выход из системы."""
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({"status": "success", "message": "Выход выполнен успешно."})
    else:
        return JsonResponse({"status": "error", "message": "Вы не авторизованы."}, status=400)

# Опционально: View для проверки статуса авторизации (может быть полезно при перезагрузке страницы)

@require_GET
def check_auth_view(request):
    if request.user.is_authenticated:
        user = request.user
        user_data = {
             "role": user.role,
             "tabel": user.tabel,
             "fio": user.fio,
        }
        return JsonResponse({"status": "authenticated", "user": user_data})
    else:
        return JsonResponse({"status": "unauthenticated"}, status=401)