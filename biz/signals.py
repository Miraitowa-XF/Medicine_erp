from django.db import transaction
from django.db.models import F, Sum
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils import timezone
from base.models import Inventory
from .models import (
    PurchaseOrder, PurchaseDetail,
    SalesOrder, SalesDetail,
    SalesReturnOrder, SalesReturnDetail,
    PurchaseReturnOrder, PurchaseReturnDetail
)

# ==========================================
# 1. 状态变更检测
# ==========================================

@receiver(pre_save, sender=PurchaseOrder)
@receiver(pre_save, sender=SalesOrder)
@receiver(pre_save, sender=SalesReturnOrder)
@receiver(pre_save, sender=PurchaseReturnOrder)
def check_status_transition(sender, instance, **kwargs):
    """
    检查单据是否是从 '其他状态' 变成了 'approved'。
    """
    if not instance.pk:
        instance._is_newly_approved = (instance.status == 'approved')
    else:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._is_newly_approved = (old_instance.status != 'approved' and instance.status == 'approved')
        except sender.DoesNotExist:
            instance._is_newly_approved = False

# ==========================================
# 2. 并发安全的核心库存操作函数
# ==========================================

def _safe_add_inventory(detail_item):
    """
    【并发安全】增加库存
    适用：进货、销售退货
    修复：自动兼容 PurchaseDetail (直连药品) 和 SalesReturnDetail (连接库存)
    """
    # 1. 动态获取 Medicine 和 BatchNumber
    # 如果是 SalesReturnDetail，它有 inventory 外键
    if hasattr(detail_item, 'inventory') and detail_item.inventory:
        target_medicine = detail_item.inventory.medicine
        # 优先用明细里记录的批号（如果有），否则用库存对象的批号
        target_batch = getattr(detail_item, 'batch_number', detail_item.inventory.batch_number)
        # 对于退货，有效期通常沿用原库存的
        target_expiry = detail_item.inventory.expiry_date
    
    # 如果是 PurchaseDetail，它直接有 medicine 外键
    elif hasattr(detail_item, 'medicine'):
        target_medicine = detail_item.medicine
        target_batch = detail_item.batch_number
        # 进货必须有有效期
        target_expiry = getattr(detail_item, 'expiry_date', timezone.now().date())
    
    else:
        raise ValueError(f"未知明细类型: {type(detail_item)}，无法获取药品信息")

    # 2. 开始事务逻辑
    with transaction.atomic():
        # 尝试查询并锁定
        inventory_qs = Inventory.objects.select_for_update().filter(
            medicine=target_medicine,
            batch_number=target_batch
        )
        
        if inventory_qs.exists():
            inventory = inventory_qs.first()
        else:
            # 如果不存在（比如新进货，或者库存被物理删除后退货回来），创建新记录
            inventory = Inventory.objects.create(
                medicine=target_medicine,
                batch_number=target_batch,
                expiry_date=target_expiry,
                quantity=0
            )
            # 重新加锁读取
            inventory = Inventory.objects.select_for_update().get(pk=inventory.pk)
        
        # 3. 原子加法
        inventory.quantity = F('quantity') + detail_item.quantity
        inventory.save()
        
        inventory.refresh_from_db()
        print(f"【并发安全加】{target_medicine.common_name} [{target_batch}] 库存变为: {inventory.quantity}")

def _safe_deduct_inventory(detail_item):
    """
    【并发安全】扣减库存
    适用：销售、采购退货
    原理：select_for_update 锁定 -> 检查余额 -> F表达式扣减
    """
    with transaction.atomic():
        # 1. 极其重要：不能直接使用 detail_item.inventory
        # 因为 detail_item.inventory 是内存里的缓存对象，没有锁。
        # 我们必须用 ID 重新去数据库里【锁定】这行记录。
        try:
            inventory = Inventory.objects.select_for_update().get(pk=detail_item.inventory.pk)
        except Inventory.DoesNotExist:
            raise ValueError(f"库存记录不存在: {detail_item.inventory}")

        # 2. 在锁的保护下检查库存（此时没人能修改它）
        if inventory.quantity < detail_item.quantity:
            # 抛出异常会触发事务回滚，单据状态保存会被撤销
            raise ValueError(
                f"并发拦截：库存不足！商品: {inventory.medicine.common_name}, "
                f"当前余: {inventory.quantity}, 需要: {detail_item.quantity}"
            )

        # 3. 原子扣减
        inventory.quantity = F('quantity') - detail_item.quantity
        inventory.save()
        
        inventory.refresh_from_db()
        print(f"【并发安全减】{inventory.medicine.common_name} [{inventory.batch_number}] 库存变为: {inventory.quantity}")


# ==========================================
# 3. 信号监听器 (调用上面的安全函数)
# ==========================================

# --- 1. 进货审核 -> 增加库存 ---
@receiver(post_save, sender=PurchaseOrder)
def stock_in_purchase(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        # 遍历所有明细，依次执行安全加法
        for item in instance.details.all():
            _safe_add_inventory(item)

# --- 2. 销售审核 -> 扣减库存 ---
@receiver(post_save, sender=SalesOrder)
def stock_out_sales(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        # 遍历所有明细，依次执行安全扣减
        for item in instance.details.all():
            _safe_deduct_inventory(item)

# --- 3. 销售退货审核 -> 增加库存 (回滚) ---
@receiver(post_save, sender=SalesReturnOrder)
def stock_in_sales_return(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        for item in instance.details.all():
            _safe_add_inventory(item)

# --- 4. 采购退货审核 -> 扣减库存 ---
@receiver(post_save, sender=PurchaseReturnOrder)
def stock_out_purchase_return(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        for item in instance.details.all():
            _safe_deduct_inventory(item)

# ==========================================
# 4. 自动计算总金额 (保持原有逻辑)
# ==========================================

def update_order_total(order_model, order_instance):
    """通用函数：计算一张单据的总金额"""
    total = order_instance.details.aggregate(total=Sum('total_amount'))['total'] or 0
    order_instance.total_amount = total
    order_instance.save(update_fields=['total_amount'])

@receiver([post_save, post_delete], sender=PurchaseDetail)
def update_purchase_total(sender, instance, **kwargs):
    update_order_total(PurchaseOrder, instance.order)

@receiver([post_save, post_delete], sender=SalesDetail)
def update_sales_total(sender, instance, **kwargs):
    update_order_total(SalesOrder, instance.order)

@receiver([post_save, post_delete], sender=SalesReturnDetail)
def update_sales_return_total(sender, instance, **kwargs):
    update_order_total(SalesReturnOrder, instance.order)

@receiver([post_save, post_delete], sender=PurchaseReturnDetail)
def update_purchase_return_total(sender, instance, **kwargs):
    update_order_total(PurchaseReturnOrder, instance.order)