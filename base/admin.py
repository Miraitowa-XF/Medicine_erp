from django.contrib import admin
from .models import Medicine, Supplier, Customer, Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'batch_number', 'quantity', 'expiry_date']
    search_fields = ['medicine__common_name', 'batch_number']

admin.site.register(Medicine)
admin.site.register(Supplier)
admin.site.register(Customer)