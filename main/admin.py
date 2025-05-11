from django.contrib import admin

from main.models import RepairRequest


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'user', 'role', 'fio', 'train', 'wagon', 'initial_description', 'repair_code', 'created_at', 'classified_by', 'classified_at')
    search_fields = ('id', 'fio', 'tabel', 'train', 'wagon', 'initial_description', 'repair_code', 'path_info')
    list_filter = ('status', 'role', 'target_role', 'created_at', 'classified_by', 'classified_at')
    list_display_links = ('id', 'initial_description')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'classified_at', 'user') # Удалены completed_at и completed_by
    fieldsets = (
        (None, {'fields': ('status', 'repair_code', 'path_info')}),
        (('Информация о неисправности'), {'fields': ('initial_description', 'fault_description')}),
        (('Данные рейса'), {'fields': ('departure_city', 'departure_date', 'train', 'wagon', 'route', 'location')}),
        (('Создатель заявки'), {'fields': ('user', 'role', 'fio', 'tabel')}),
        (('Адресат'), {'fields': ('target_role',)}),
        (('История обработки'), {'fields': ('classified_by', 'classified_at')}), # Удалены completed_by и completed_at
        (('Даты'), {'fields': ('created_at',)}),
    )


