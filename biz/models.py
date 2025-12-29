from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import CheckConstraint, Q, F

# 状态常量
STATUS_CHOICES = [
    ('pending', '待审核'),
    ('approved', '已审核/执行'),
    ('cancelled', '已作废'),
]

# ==========================================
# 1. 进货业务 (Purchase)
# ==========================================

class PurchaseOrder(models.Model):
    """进货单头"""
    supplier = models.ForeignKey('base.Supplier', on_delete=models.CASCADE, verbose_name="供应商")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="经办人")
    
    order_date = models.DateTimeField("进货日期", default=timezone.now)
    total_amount = models.DecimalField("总金额", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = "进货单"
        verbose_name_plural = verbose_name
        ordering = ['-order_date']
        indexes = [
            # 经常查某个日期的订单
            models.Index(fields=['order_date'], name='idx_purchase_date'),
            # 经常查某种状态的订单（如：只看 Pending 的）
            models.Index(fields=['status'], name='idx_purchase_status'),
            # 联合索引：加速查询 "某供应商的某状态订单"
            models.Index(fields=['supplier', 'status'], name='idx_purch_sup_status'),
        ]

    def __str__(self):
        return f"PO-{self.id} | {self.supplier.name}"

class PurchaseDetail(models.Model):
    """进货明细"""
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='details', verbose_name="关联单据")
    
    # 核心：进货连 Medicine (无中生有)
    medicine = models.ForeignKey('base.Medicine', on_delete=models.CASCADE, verbose_name="药品")
    
    batch_number = models.CharField("生产批号", max_length=50)
    produce_date = models.DateField("生产日期")
    expiry_date = models.DateField("有效期")
    
    quantity = models.PositiveIntegerField("数量", default=0)
    unit_price = models.DecimalField("实际进价", max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField("小计", max_digits=12, decimal_places=2, editable=False, default=0)

    class Meta:
        verbose_name = "进货明细"
        verbose_name_plural = verbose_name
        constraints = [
            # 约束 1: 单价和数量必须 >= 0
            CheckConstraint(
                condition=Q(unit_price__gte=0) & Q(quantity__gte=0), 
                name='check_purchase_price_qty_positive'
            ),
            # 约束 2: 有效期必须 > 生产日期 (这是数据库层面的逻辑校验！)
            CheckConstraint(
                condition=Q(expiry_date__gt=F('produce_date')), 
                name='check_expiry_after_produce'
            ),
        ]

    def save(self, *args, **kwargs):
        # 修正：增加空值判断，防止未填写时报错
        qty = self.quantity or 0
        price = self.unit_price or 0
        self.total_amount = qty * price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medicine} ({self.batch_number})"

# ==========================================
# 2. 销售业务 (Sales)
# ==========================================

class SalesOrder(models.Model):
    """销售单头"""
    customer = models.ForeignKey('base.Customer', on_delete=models.CASCADE, verbose_name="客户")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="销售员")
    
    order_date = models.DateTimeField("销售日期", default=timezone.now)
    total_amount = models.DecimalField("总金额", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = "销售单"
        verbose_name_plural = verbose_name
        ordering = ['-order_date']
        indexes = [
            # 经常查某个日期的订单
            models.Index(fields=['order_date'], name='idx_sales_date'),
            # 经常查某种状态的订单（如：只看 Pending 的）
            models.Index(fields=['status'], name='idx_sales_status'),
        ]

    def __str__(self):
        return f"SO-{self.id} | {self.customer.name}"

class SalesDetail(models.Model):
    """销售明细"""
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='details', verbose_name="关联单据")
    
    # 核心：销售连 Inventory (有的放矢)
    inventory = models.ForeignKey('base.Inventory', on_delete=models.CASCADE, verbose_name="源库存")
    
    # 冗余存储批号，防止 Inventory 记录被物理删除后查不到历史
    batch_number_snapshot = models.CharField("批号快照", max_length=50, blank=True)
    
    quantity = models.PositiveIntegerField("数量", default=0)
    actual_price = models.DecimalField("实际成交价", max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField("小计", max_digits=12, decimal_places=2, editable=False, default=0)

    class Meta:
        verbose_name = "销售明细"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        # 修正：增加空值判断
        qty = self.quantity or 0
        price = self.actual_price or 0
        self.total_amount = qty * price
        
        # 自动保存快照 (确保 inventory 存在)
        if self.inventory_id and not self.batch_number_snapshot:
            # 注意：这里直接访问 self.inventory 可能会触发数据库查询
            # 使用 inventory_id 判断更安全
            try:
                self.batch_number_snapshot = self.inventory.batch_number
            except:
                pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Out: {self.inventory.medicine} * {self.quantity}"

# ==========================================
# 3. 销售退货业务 (Sales Return)
# ==========================================

class SalesReturnOrder(models.Model):
    """销售退货单 (顾客退给药店)"""
    customer = models.ForeignKey('base.Customer', on_delete=models.CASCADE, verbose_name="退货客户")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="经办人")
    
    return_date = models.DateTimeField("退货日期", default=timezone.now)
    total_amount = models.DecimalField("退款总额", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = "销售退货单"
        verbose_name_plural = verbose_name
        ordering = ['-return_date']
        indexes = [
            # 经常查某个日期的订单
            models.Index(fields=['return_date'], name='idx_sales_return_date'),
            # 经常查某种状态的订单（如：只看 Pending 的）
            models.Index(fields=['status'], name='idx_sales_return_status'),
        ]

    def __str__(self):
        return f"SR-{self.id} | {self.customer.name}"

class SalesReturnDetail(models.Model):
    """销售退货明细"""
    order = models.ForeignKey(SalesReturnOrder, on_delete=models.CASCADE, related_name='details', verbose_name="关联单据")
    
    # 核心：退货连 Inventory (回到库存)
    inventory = models.ForeignKey('base.Inventory', on_delete=models.CASCADE, verbose_name="归还至库存")
    
    quantity = models.PositiveIntegerField("数量", default=0)
    refund_price = models.DecimalField("退款单价", max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField("小计", max_digits=12, decimal_places=2, editable=False, default=0)

    class Meta:
        verbose_name = "销售退货明细"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        qty = self.quantity or 0
        price = self.refund_price or 0
        self.total_amount = qty * price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Return: {self.inventory.medicine} * {self.quantity}"

# ==========================================
# 4. 采购退货业务 (Purchase Return)
# ==========================================

class PurchaseReturnOrder(models.Model):
    """采购退货单 (药店退给供应商)"""
    supplier = models.ForeignKey('base.Supplier', on_delete=models.CASCADE, verbose_name="供应商")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="经办人")
    
    return_date = models.DateTimeField("退货日期", default=timezone.now)
    total_amount = models.DecimalField("退款总额", max_digits=12, decimal_places=2, default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = "采购退货单"
        verbose_name_plural = verbose_name
        ordering = ['-return_date']
        indexes = [
            # 经常查某个日期的订单
            models.Index(fields=['return_date'], name='idx_purchase_return_date'),
            # 经常查某种状态的订单（如：只看 Pending 的）
            models.Index(fields=['status'], name='idx_purchase_return_status'),
        ]

    def __str__(self):
        return f"PR-{self.id} | {self.supplier.name}"

class PurchaseReturnDetail(models.Model):
    """采购退货明细"""
    order = models.ForeignKey(PurchaseReturnOrder, on_delete=models.CASCADE, related_name='details', verbose_name="关联单据")
    
    # 核心：退货连 Inventory (从库存扣除)
    inventory = models.ForeignKey('base.Inventory', on_delete=models.CASCADE, verbose_name="扣减库存")
    
    quantity = models.PositiveIntegerField("数量", default=0)
    unit_price = models.DecimalField("退货单价", max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField("小计", max_digits=12, decimal_places=2, editable=False, default=0)

    class Meta:
        verbose_name = "采购退货明细"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        qty = self.quantity or 0
        price = self.unit_price or 0
        self.total_amount = qty * price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Deduct: {self.inventory.medicine} * {self.quantity}"