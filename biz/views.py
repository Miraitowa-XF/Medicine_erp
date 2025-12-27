from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PurchaseOrder

@login_required
def purchase_list(request):
    """采购订单列表视图"""
    # 获取所有采购单，预加载供应商和经办人
    orders = PurchaseOrder.objects.select_related('supplier', 'employee').all().order_by('-order_date')
    
    context = {
        'orders': orders,
    }
    return render(request, 'biz/purchase_list.html', context)
