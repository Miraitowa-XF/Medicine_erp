from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.db import transaction
from base.models import Inventory
from .models import (
    PurchaseOrder, PurchaseDetail,
    SalesOrder, SalesDetail,
    SalesReturnOrder, SalesReturnDetail,
    PurchaseReturnOrder, PurchaseReturnDetail
)

# ==========================================
# 核心修复：状态变更检测 (通用逻辑)
# ==========================================

# 将四个单据模型打包，统一监听
OrderModels = [PurchaseOrder, SalesOrder, SalesReturnOrder, PurchaseReturnOrder]

@receiver(pre_save, sender=PurchaseOrder)
@receiver(pre_save, sender=SalesOrder)
@receiver(pre_save, sender=SalesReturnOrder)
@receiver(pre_save, sender=PurchaseReturnOrder)
def check_status_transition(sender, instance, **kwargs):
    """
    在保存之前执行：
    检查单据是否是从 '其他状态' 变成了 'approved'。
    我们将结果存在 instance 的一个临时属性 _is_newly_approved 中，
    供后面的 post_save 使用。
    """
    # 如果没有主键(pk)，说明是新创建的单据
    if not instance.pk:
        # 如果一创建就是 approved (虽然很少见)，标记为 True
        instance._is_newly_approved = (instance.status == 'approved')
    else:
        # 如果是修改已有单据，去数据库里查一下“旧的状态”是什么
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            # 只有当：旧状态不是approved 且 新状态是approved 时，才算“新批准”
            instance._is_newly_approved = (old_instance.status != 'approved' and instance.status == 'approved')
        except sender.DoesNotExist:
            instance._is_newly_approved = False

# ==========================================
# 库存更新逻辑 (修正版)
# ==========================================

# 1. 进货审核 -> 增加库存
@receiver(post_save, sender=PurchaseOrder)
def stock_in_purchase(sender, instance, **kwargs):
    # 修正：检查临时标记，只有“刚刚变成Approved”时才执行
    if getattr(instance, '_is_newly_approved', False):
        with transaction.atomic():
            for item in instance.details.all():
                inventory, created = Inventory.objects.get_or_create(
                    medicine=item.medicine,
                    batch_number=item.batch_number,
                    defaults={
                        'expiry_date': item.expiry_date,
                        'quantity': 0
                    }
                )
                inventory.quantity += item.quantity
                inventory.save()
                print(f"【进货生效】库存更新: {inventory} +{item.quantity}")

# 2. 销售审核 -> 扣减库存
@receiver(post_save, sender=SalesOrder)
def stock_out_sales(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        with transaction.atomic():
            for item in instance.details.all():
                inventory = item.inventory
                if inventory.quantity < item.quantity:
                    # 注意：如果库存不足，这里抛出异常会回滚事务，保存失败
                    raise ValueError(f"库存不足: {inventory} 剩余 {inventory.quantity}, 需要 {item.quantity}")
                
                inventory.quantity -= item.quantity
                inventory.save()
                print(f"【销售生效】库存更新: {inventory} -{item.quantity}")

# 3. 销售退货审核 -> 增加库存 (回滚)
@receiver(post_save, sender=SalesReturnOrder)
def stock_in_sales_return(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        with transaction.atomic():
            for item in instance.details.all():
                inventory = item.inventory
                inventory.quantity += item.quantity
                inventory.save()
                print(f"【销售退货生效】库存更新: {inventory} +{item.quantity}")

# 4. 采购退货审核 -> 扣减库存
@receiver(post_save, sender=PurchaseReturnOrder)
def stock_out_purchase_return(sender, instance, **kwargs):
    if getattr(instance, '_is_newly_approved', False):
        with transaction.atomic():
            for item in instance.details.all():
                inventory = item.inventory
                if inventory.quantity < item.quantity:
                    raise ValueError(f"退货失败，库存不足: {inventory}")
                
                inventory.quantity -= item.quantity
                inventory.save()
                print(f"【采购退货生效】库存更新: {inventory} -{item.quantity}")

# ==========================================
# 自动计算总金额 (Total Amount) 逻辑
# 注意：金额计算不需要限制“只执行一次”，每次修改明细都应该重算
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