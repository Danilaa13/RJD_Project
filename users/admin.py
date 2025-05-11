from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserRole




class CustomUserAdmin(UserAdmin):
    """
    Настройка отображения модели CustomUser в панели администратора.
    Наследуется от стандартного UserAdmin для сохранения базовых полей пользователя.
    """

    list_display = UserAdmin.list_display + ('role', 'tabel', 'fio')
    list_filter = UserAdmin.list_filter + ('role', 'is_staff', 'is_superuser', 'is_active')

    # Определяем, по каким полям можно будет искать пользователей
    search_fields = UserAdmin.search_fields + ('tabel', 'fio', 'role')

    # Определяем разделы и поля на странице редактирования существующего пользователя
    fieldsets = UserAdmin.fieldsets + (
        # Добавляем новый раздел для ваших кастомных полей
        ('Custom fields', {'fields': ('role', 'tabel', 'fio')}),
        # Если у вас есть другие кастомные поля, добавьте их сюда
    )

    # Определяем разделы и поля на странице создания нового пользователя
    # UserAdmin.add_fieldsets по умолчанию включает только ('username', 'password', 'password2')
    add_fieldsets = UserAdmin.add_fieldsets + (
        # Добавляем раздел с вашими кастомными полями при создании нового пользователя
        ('Custom fields', {'fields': ('role', 'tabel', 'fio')}),
    )




admin.site.register(CustomUser, CustomUserAdmin)

