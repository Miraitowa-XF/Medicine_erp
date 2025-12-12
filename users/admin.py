from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    list_display = ('username', 'real_name', 'position', 'mobile', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('员工信息', {'fields': ('real_name', 'mobile', 'position')}),
    )
