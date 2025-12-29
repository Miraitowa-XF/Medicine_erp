from django.shortcuts import render
<<<<<<< Updated upstream

# Create your views here.
=======
from django.contrib.auth.decorators import login_required
from .models import PurchaseOrder, SalesOrder
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@login_required
def purchase_list(request):
    """采购订单列表视图"""
    # 获取所有采购单，预加载供应商和经办人
    orders = PurchaseOrder.objects.select_related('supplier', 'employee').all().order_by('-order_date')
    
    context = {
        'orders': orders,
    }
    return render(request, 'biz/purchase_list.html', context)

@login_required
def sales_list(request):
    """销售订单列表视图"""
    # 获取所有销售单，预加载客户和销售员
    orders = SalesOrder.objects.select_related('customer', 'employee').all().order_by('-order_date')
    
    context = {
        'orders': orders,
    }
    return render(request, 'biz/sales_list.html', context)

@login_required
def finance_report(request):
    """财务报表视图"""
    # 计算最近30天的统计数据
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # 采购统计
    purchase_stats = PurchaseOrder.objects.filter(order_date__gte=thirty_days_ago).aggregate(
        total_orders=Count('id'),
        total_amount=Sum('total_amount')
    )
    
    # 销售统计
    sales_stats = SalesOrder.objects.filter(order_date__gte=thirty_days_ago).aggregate(
        total_orders=Count('id'),
        total_amount=Sum('total_amount')
    )
    
    # 利润计算（简化版：销售总额 - 采购总额）
    profit = (sales_stats['total_amount'] or 0) - (purchase_stats['total_amount'] or 0)
    
    context = {
        'purchase_stats': purchase_stats,
        'sales_stats': sales_stats,
        'profit': profit,
        'period': '最近30天',
    }
    return render(request, 'biz/finance_report.html', context)
>>>>>>> Stashed changes
