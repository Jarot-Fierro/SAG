from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin


class StandardAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='¿Activo?', boolean=True)
    def active_status(self, obj):
        return obj.is_active

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if 'active_status' not in list_display:
            if isinstance(list_display, tuple):
                list_display = list_display + ('active_status',)
            else:
                list_display = list(list_display)
                list_display.append('active_status')
        return list_display
