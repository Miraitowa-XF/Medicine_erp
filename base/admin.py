from django.contrib import admin
from .models import Medicine, Supplier, Customer, Inventory, SupplierPhone

# 定义电话的内联显示
class SupplierPhoneInline(admin.TabularInline):
    model = SupplierPhone
    extra = 1  # 默认显示一行空的，方便添加

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    # 把电话表嵌入到供应商管理页面中
    inlines = [SupplierPhoneInline]
    
    list_display = ['name', 'contact_person', 'license_no', 'show_phones']
    search_fields = ['name', 'contact_person', 'phones__number'] # 支持直接搜电话号码！

    # 自定义方法：在列表页显示所有电话
    def show_phones(self, obj):
        # 将该供应商的所有电话拼成字符串显示
        return ", ".join([p.number for p in obj.phones.all()])
    show_phones.short_description = "联系方式"

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'batch_number', 'quantity', 'expiry_date']
    search_fields = ['medicine__common_name', 'batch_number']

admin.site.register(Medicine)
# admin.site.register(Supplier)  
admin.site.register(Customer)