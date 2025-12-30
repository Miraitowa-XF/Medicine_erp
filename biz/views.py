from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PurchaseOrder, SalesOrder
from .forms import PurchaseOrderForm, SalesOrderForm, PurchaseDetailFormSet, SalesDetailFormSet
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

# Helper to check permissions
def can_manage_orders(user):
    # Salesperson can insert/update/modify bills in Purchase Order and Sales Order interfaces
    return user.position in ['sales', 'manager', 'purchaser']

def can_view_finance_data(user):
    # Finance can view Purchase Order, Sales Order, Customer and Supplier
    return user.position in ['finance', 'manager']

@login_required
def purchase_list(request):
    """采购订单列表视图"""
    orders = PurchaseOrder.objects.select_related('supplier', 'employee').prefetch_related('details__medicine').all().order_by('-order_date')
    
    context = {
        'orders': orders,
        'can_edit': can_manage_orders(request.user)
    }
    return render(request, 'biz/purchase_list.html', context)

@login_required
def purchase_create(request):
    if not can_manage_orders(request.user):
        messages.error(request, '无权限创建采购单')
        return redirect('purchase_list')
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.employee = request.user
            order.save()
            formset.instance = order
            formset.save()
            # 更新总金额
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '采购单已创建')
            return redirect('purchase_list')
    else:
        form = PurchaseOrderForm()
        formset = PurchaseDetailFormSet()
    return render(request, 'biz/purchase_form.html', {'form': form, 'formset': formset, 'title': '新建采购单'})

@login_required
def purchase_edit(request, pk):
    if not can_manage_orders(request.user):
        messages.error(request, '无权限修改采购单')
        return redirect('purchase_list')
        
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=order)
        formset = PurchaseDetailFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            # 更新总金额
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '采购单已更新')
            return redirect('purchase_list')
    else:
        form = PurchaseOrderForm(instance=order)
        formset = PurchaseDetailFormSet(instance=order)
    return render(request, 'biz/purchase_form.html', {'form': form, 'formset': formset, 'title': '编辑采购单', 'order': order})

@login_required
def sales_list(request):
    """销售订单列表视图"""
    orders = SalesOrder.objects.select_related('customer', 'employee').prefetch_related('details__inventory__medicine').all().order_by('-order_date')
    
    context = {
        'orders': orders,
        'can_edit': can_manage_orders(request.user)
    }
    return render(request, 'biz/sales_list.html', context)

@login_required
def sales_create(request):
    if not can_manage_orders(request.user):
        messages.error(request, '无权限创建销售单')
        return redirect('sales_list')

    if request.method == 'POST':
        form = SalesOrderForm(request.POST)
        formset = SalesDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.employee = request.user
            order.save()
            formset.instance = order
            formset.save()
            # 更新总金额
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '销售单已创建')
            return redirect('sales_list')
    else:
        form = SalesOrderForm()
        formset = SalesDetailFormSet()
    return render(request, 'biz/sales_form.html', {'form': form, 'formset': formset, 'title': '新建销售单'})

@login_required
def sales_edit(request, pk):
    if not can_manage_orders(request.user):
        messages.error(request, '无权限修改销售单')
        return redirect('sales_list')
        
    order = get_object_or_404(SalesOrder, pk=pk)
    if request.method == 'POST':
        form = SalesOrderForm(request.POST, instance=order)
        formset = SalesDetailFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            # 更新总金额
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '销售单已更新')
            return redirect('sales_list')
    else:
        form = SalesOrderForm(instance=order)
        formset = SalesDetailFormSet(instance=order)
    return render(request, 'biz/sales_form.html', {'form': form, 'formset': formset, 'title': '编辑销售单', 'order': order})

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
