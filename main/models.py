from django.db import models
from django.utils import timezone
from django.urls import reverse

class RepairRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('assigned', 'В наряде'),
        ('done', 'Выполнено'),
        ('urgent', 'Срочная'), # Добавим "Срочная" как возможный статус
    ]

    # Информация о сотруднике и поезде (из формы)
    employee_fio = models.CharField("ФИО сотрудника", max_length=200)
    employee_tabel = models.CharField("Табельный номер", max_length=50)
    train_number = models.CharField("Номер поезда", max_length=50)
    wagon_number = models.CharField("Номер вагона", max_length=100) # Увеличил длину для формата 001-07656

    # Информация о неисправности (из JS навигации)
    category_path = models.TextField("Путь по категориям") # Храним весь путь как строку
    fault_description = models.CharField("Описание неисправности", max_length=255) # Последний выбранный элемент
    classification_code = models.CharField("Код классификатора", max_length=20)

    # Метаданные заявки
    created_at = models.DateTimeField("Время создания", default=timezone.now)
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default='new')
    deadline = models.DateTimeField("Срок выполнения", null=True, blank=True) # Сделаем необязательным, будем вычислять

    # Дополнительные поля для соответствия панели (можно заполнять позже или сделать необязательными)
    route = models.CharField("Маршрут", max_length=255, blank=True, null=True)
    location = models.CharField("Пункт", max_length=255, blank=True, null=True)
    # assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks') # Если есть система пользователей

    def __str__(self):
        return f"Заявка {self.id} от {self.employee_fio} (Вагон: {self.wagon_number})"

    def get_absolute_url(self):
        # Полезно для перенаправлений или ссылок, например, на страницу детализации
        # return reverse('request_detail', kwargs={'pk': self.pk})
        return reverse('dispatcher_panel') # После создания заявки перейдем на панель

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
        if not self.deadline:
            self.deadline = self.calculate_default_deadline()
        super().save(*args, **kwargs)