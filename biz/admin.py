from django.contrib import admin
from .models import (
    PurchaseOrder, PurchaseDetail,
    SalesOrder, SalesDetail,
    SalesReturnOrder, SalesReturnDetail,
    PurchaseReturnOrder, PurchaseReturnDetail
)

# ==========================================
# 1. 进货业务 Admin 配置
# ==========================================

class PurchaseDetailInline(admin.TabularInline):
    """进货单明细内联"""
    model = PurchaseDetail
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """进货单管理"""
    inlines = [PurchaseDetailInline]
    list_display = ['id', 'supplier', 'employee', 'total_amount', 'status', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['id', 'supplier__name']
    
    # 默认只读字段
    readonly_fields = ['total_amount']

    def get_readonly_fields(self, request, obj=None):
        """
        方案 C 核心逻辑：
        如果是新建单据 (obj is None)，强制锁定 'status' 为只读。
        这迫使必须先保存单据(Pending)，确保明细写入数据库后，
        才能在第二次编辑时修改状态为 Approved，从而触发库存更新信号。
        """
        if obj is None:
            return ['status', 'total_amount']
        return self.readonly_fields

# ==========================================
# 2. 销售业务 Admin 配置
# ==========================================

class SalesDetailInline(admin.TabularInline):
    """销售单明细内联"""
    model = SalesDetail
    extra = 1

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    """销售单管理"""
    inlines = [SalesDetailInline]
    list_display = ['id', 'customer', 'employee', 'total_amount', 'status', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['id', 'customer__name']
    
    readonly_fields = ['total_amount']

    def get_readonly_fields(self, request, obj=None):
        """新建时锁定状态，防止直接审核导致库存不扣减 bug"""
        if obj is None:
            return ['status', 'total_amount']
        return self.readonly_fields

# ==========================================
# 3. 销售退货业务 Admin 配置
# ==========================================

class SalesReturnDetailInline(admin.TabularInline):
    """销售退货明细内联"""
    model = SalesReturnDetail
    extra = 1

@admin.register(SalesReturnOrder)
class SalesReturnOrderAdmin(admin.ModelAdmin):
    """销售退货单管理"""
    inlines = [SalesReturnDetailInline]
    list_display = ['id', 'customer', 'employee', 'total_amount', 'status', 'return_date']
    list_filter = ['status', 'return_date']
    search_fields = ['id', 'customer__name']
    
    readonly_fields = ['total_amount']

    def get_readonly_fields(self, request, obj=None):
        """新建时锁定状态"""
        if obj is None:
            return ['status', 'total_amount']
        return self.readonly_fields

# ==========================================
# 4. 采购退货业务 Admin 配置
# ==========================================

class PurchaseReturnDetailInline(admin.TabularInline):
    """采购退货明细内联"""
    model = PurchaseReturnDetail
    extra = 1

@admin.register(PurchaseReturnOrder)
class PurchaseReturnOrderAdmin(admin.ModelAdmin):
    """采购退货单管理"""
    inlines = [PurchaseReturnDetailInline]
    list_display = ['id', 'supplier', 'employee', 'total_amount', 'status', 'return_date']
    list_filter = ['status', 'return_date']
    search_fields = ['id', 'supplier__name']
    
    readonly_fields = ['total_amount']

    def get_readonly_fields(self, request, obj=None):
        """新建时锁定状态"""
        if obj is None:
            return ['status', 'total_amount']
        return self.readonly_fields