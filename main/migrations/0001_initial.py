# Generated by Django 5.2 on 2025-05-06 10:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RepairRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=50, verbose_name='Роль создателя')),
                ('tabel', models.CharField(max_length=20, verbose_name='Табельный номер создателя')),
                ('fio', models.CharField(max_length=255, verbose_name='ФИО создателя')),
                ('departure_city', models.CharField(blank=True, max_length=100, null=True, verbose_name='Город отправления')),
                ('departure_date', models.DateField(blank=True, null=True, verbose_name='Дата отправления')),
                ('train', models.CharField(blank=True, max_length=50, null=True, verbose_name='Поезд')),
                ('wagon', models.CharField(blank=True, max_length=50, null=True, verbose_name='Вагон')),
                ('target_role', models.CharField(blank=True, choices=[('Проводник', 'Проводник'), ('ПЭМ', 'ПЭМ'), ('ПДК', 'Диспетчер'), ('Ревизор', 'Ревизор'), ('Администратор', 'Администратор')], max_length=50, null=True, verbose_name='Адресат заявки')),
                ('initial_description', models.TextField(blank=True, null=True, verbose_name='Первичное описание')),
                ('classified_at', models.DateTimeField(blank=True, null=True, verbose_name='Время классификации')),
                ('path_info', models.TextField(verbose_name='Путь неисправности (JSON)')),
                ('repair_code', models.CharField(blank=True, max_length=10, null=True, verbose_name='Код неисправности')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')),
                ('status', models.CharField(choices=[('pending', 'В ожидании'), ('assigned', 'В наряде'), ('in_progress', 'В работе'), ('classified', 'Классифицирована'), ('completed', 'Выполнена'), ('cancelled', 'Отменена')], default='pending', max_length=20, verbose_name='Статус')),
                ('route', models.CharField(blank=True, max_length=255, null=True, verbose_name='Маршрут')),
                ('location', models.CharField(blank=True, max_length=255, null=True, verbose_name='Пункт')),
            ],
            options={
                'verbose_name': 'Заявка на ремонт',
                'verbose_name_plural': 'Заявки на ремонт',
                'ordering': ['-created_at'],
            },
        ),
    ]
