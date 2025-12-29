from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Employee
from django.contrib.auth.models import Group  # 引入原生 Group
from .models import Employee, ProxyGroup      # 引入刚才定义的 ProxyGroup

# 1. 注销原生的 Group (让它从 AUTHENTICATION AND AUTHORIZATION 下面消失)
admin.site.unregister(Group)

@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    list_display = ('username', 'real_name', 'position', 'mobile', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('员工信息', {'fields': ('real_name', 'mobile', 'position')}),
    )

# 3. 注册代理 Group (让它显示在你的 Users App 下面)
@admin.register(ProxyGroup)
class ProxyGroupAdmin(admin.ModelAdmin):
    # 直接使用原生 Group 的字段
    list_display = ['name']
    search_fields = ['name']
    filter_horizontal = ['permissions'] # 权限选择框样式优化