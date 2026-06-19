from django.contrib import admin
from .models import CustomUser, CustomRole, AppSection, AppPermission, RolePermission, AuditLog, Record
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(CustomRole)
admin.site.register(AppSection)
admin.site.register(AppPermission)
admin.site.register(RolePermission)
admin.site.register(AuditLog)
admin.site.register(Record)