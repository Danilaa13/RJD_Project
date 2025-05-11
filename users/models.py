from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _ # Для локализации

class UserRole(models.TextChoices):
    """Определяет возможные роли пользователей."""
    CONDUCTOR = 'Проводник', _('Проводник')
    PEM = 'ПЭМ', _('ПЭМ')
    DISPATCHER = 'ПДК', _('Диспетчер')
    REVISOR = 'Ревизор', _('Ревизор')
    ADMIN = 'Администратор', _('Администратор')
    # Добавьте другие роли, если необходимо

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя с полями для роли, табельного номера и ФИО.
    Унаследована от AbstractUser для использования встроенной системы аутентификации Django.
    """

    role = models.CharField(
        max_length=50,
        choices=UserRole.choices,
        default=UserRole.CONDUCTOR,
        verbose_name=_('Роль')
    )
    tabel = models.CharField(max_length=20, verbose_name=_('Табельный номер')) # Не делаем его уникальным здесь
    fio = models.CharField(max_length=255, verbose_name=_('ФИО'))

    # Добавляем уникальное ограничение на комбинацию role и tabel
    class Meta:
        # Используем UniqueConstraint для гарантии уникальности пары (role, tabel)
        constraints = [
            UniqueConstraint(fields=['role', 'tabel'], name='unique_role_tabel')
        ]
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return f"{self.get_role_display()} - {self.fio} ({self.tabel})"

