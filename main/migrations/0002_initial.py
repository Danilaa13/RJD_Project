# Generated by Django 5.2 on 2025-05-06 10:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='repairrequest',
            name='classified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classified_requests', to=settings.AUTH_USER_MODEL, verbose_name='Классифицировал (ПЭМ)'),
        ),
        migrations.AddField(
            model_name='repairrequest',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_repair_requests', to=settings.AUTH_USER_MODEL, verbose_name='Создал заявку'),
        ),
    ]
