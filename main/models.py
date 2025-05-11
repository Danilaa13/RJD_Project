from users.models import CustomUser, UserRole
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import json


class RequestStatus(models.TextChoices):
    PENDING = 'pending', _('В ожидании')  # Ожидает назначения/классификации
    ASSIGNED = 'assigned', _('В наряде')  # Назначена исполнителю (может быть и ПЭМ, и слесарь)
    IN_PROGRESS = 'in_progress', _('В работе')  # Активно выполняется
    CLASSIFIED = 'classified', _('Классифицирована')  # ПЭМ определил тип, ожидает ПДК
    COMPLETED = 'completed', _('Выполнена')  # Завершено успешно
    CANCELLED = 'cancelled', _('Отменена')  # Отменена
    URGENT = 'urgent', _('Срочная')

    # Убрал URGENT как статус, срочность лучше делать отдельным флагом или приоритетом


class RepairRequest(models.Model):
    # Связь с пользователем, создавшим заявку
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_repair_requests',  # Изменил related_name для ясности
        verbose_name=_('Создал заявку')
    )
    # Информация о создателе (дублируется для истории, если user удален)
    role = models.CharField(max_length=50, verbose_name=_('Роль создателя'))
    tabel = models.CharField(max_length=20, verbose_name=_('Табельный номер создателя'))
    fio = models.CharField(max_length=255, verbose_name=_('ФИО создателя'))

    # Информация о рейсе (обязательна для Проводника/ПЭМ при создании)
    departure_city = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('Город отправления'))
    departure_date = models.DateField(null=True, blank=True, verbose_name=_('Дата отправления'))
    train = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Поезд'))
    wagon = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Вагон'))

    # --- НОВЫЕ ПОЛЯ ---
    # Кому адресована заявка ИЗНАЧАЛЬНО (выбор Проводника)
    target_role = models.CharField(
        max_length=50,
        choices=UserRole.choices,  # Используем те же роли
        null=True,  # Может быть null, если создается не Проводником или уже обработано
        blank=True,
        verbose_name=_('Адресат заявки')
    )
    # Описание неисправности, данное пользователем (опционально, можно генерировать)
    initial_description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Первичное описание")
        # Можно заполнять из последнего элемента path_info при сохранении, если нужно
    )
    # Кем была классифицирована заявка (если ПЭМ)
    classified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classified_requests',
        verbose_name=_('Классифицировал (ПЭМ)')
    )
    classified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Время классификации")
    )
    # --- КОНЕЦ НОВЫХ ПОЛЕЙ ---

    # Информация о неисправности (путь и код могут обновляться ПЭМ)
    path_info = models.TextField(verbose_name=_('Путь неисправности (JSON)'))
    repair_code = models.CharField(max_length=10, verbose_name=_('Код неисправности'), blank=True,
                                   null=True)  # Может быть пустым до классификации ПЭМ

    # Метаданные заявки
    created_at = models.DateTimeField("Время создания", default=timezone.now)
    updated_at = models.DateTimeField("Последнее обновление", auto_now=True)  # Полезно для отслеживания
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING  # Новый статус по умолчанию
    )
    # Убрал deadline, так как логика его расчета может быть сложной и зависеть от классификации
    # deadline = models.DateTimeField("Срок выполнения", null=True, blank=True)

    # Дополнительные поля (оставим как есть)
    route = models.CharField("Маршрут", max_length=255, blank=True, null=True)
    location = models.CharField("Пункт", max_length=255, blank=True, null=True)

    # assigned_to = models.ForeignKey(CustomUser, ...) # Можно добавить поле для конкретного исполнителя

    def __str__(self):
        target = f" -> {self.get_target_role_display()}" if self.target_role else ""
        return f"Заявка {self.pk} от {self.fio} ({self.role}{target}) - Статус: {self.get_status_display()}"

    class Meta:
        verbose_name = "Заявка на ремонт"
        verbose_name_plural = "Заявки на ремонт"
        ordering = ['-created_at']

    @property
    def fault_description(self):
        """Генерирует краткое описание неисправности."""
        # Используем первичное описание, если оно есть
        if self.initial_description:
            return self.initial_description
        # Иначе пытаемся получить из path_info
        try:
            path_list = json.loads(self.path_info or '[]')
            if isinstance(path_list, list) and len(path_list) > 0:
                # Возвращаем последний элемент пути как описание
                return str(path_list[-1])
            else:
                return self.repair_code or "Нет описания"
        except (json.JSONDecodeError, TypeError):
            return self.repair_code or "Ошибка описания"