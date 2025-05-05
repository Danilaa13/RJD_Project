from users.models import CustomUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
import json



class RequestStatus(models.TextChoices):

    PENDING = 'pending', 'В ожидании'
    IN_PROGRESS = 'in_progress', 'В работе'
    COMPLETED = 'completed', 'Выполнена'
    CANCELLED = 'cancelled', 'Отменена'
    URGENT = 'urgent', 'Срочная'


class RepairRequest(models.Model):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repair_requests',
        verbose_name=_('Пользователь')
    )

    role = models.CharField(max_length=50, verbose_name=_('Роль'))
    tabel = models.CharField(max_length=20, verbose_name=_('Табельный номер'))
    fio = models.CharField(max_length=255, verbose_name=_('ФИО'))
    departure_city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('Город отправления')
    )
    departure_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Дата отправления')
    )
    train = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Поезд')
    )
    wagon = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Вагон')
    )

    # Информация о неисправности (из JS навигации)
    path_info = models.TextField(verbose_name=_('Путь неисправности'))
    repair_code = models.CharField(max_length=10, verbose_name=_('Код неисправности'))

    fault_description = models.CharField(
        "Описание неисправности",  # Название в админке
        max_length=255,  # Максимальная длина (можно увеличить, если нужно)
        blank=True,  # Разрешить быть пустым (если по какой-то причине не удалось определить)
        null=True  # Разрешить быть NULL в базе данных
    )

    # Метаданные заявки
    created_at = models.DateTimeField("Время создания", default=timezone.now)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )
    deadline = models.DateTimeField("Срок выполнения", null=True, blank=True) # Сделаем необязательным, будем вычислять

    # Дополнительные поля для соответствия панели (можно заполнять позже или сделать необязательными)
    route = models.CharField("Маршрут", max_length=255, blank=True, null=True)
    location = models.CharField("Пункт", max_length=255, blank=True, null=True)
    # assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks') # Если есть система пользователей

    def __str__(self):
        return f"Заявка {self.pk} от {self.fio} ({self.role}) - Код: {self.repair_code}"


    class Meta:
        verbose_name = "Заявка на ремонт"
        verbose_name_plural = "Заявки на ремонт"
        ordering = ['-created_at'] # Сортируем по умолчанию: новые сверху

    # Пример метода для вычисления срока (можно вызвать при сохранении)
    def calculate_default_deadline(self):
        # Пример: 24 часа на обычную, 4 часа на срочную (если статус 'urgent')
        if self.status == 'urgent':
            return self.created_at + timezone.timedelta(hours=4)
        else:
            return self.created_at + timezone.timedelta(hours=24)

    # Переопределим save, чтобы установить deadline, если он не задан
    def save(self, *args, **kwargs):
        if not self.deadline and self.created_at:
             if self.status == RequestStatus.URGENT:
                 self.deadline = self.created_at + timezone.timedelta(hours=4)
             else:
                 self.deadline = self.created_at + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)