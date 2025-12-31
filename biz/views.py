from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    PurchaseOrder, SalesOrder,
    PurchaseReturnOrder, SalesReturnOrder
)
from .forms import (
    PurchaseOrderForm, SalesOrderForm, PurchaseDetailFormSet, SalesDetailFormSet,
    PurchaseReturnOrderForm, SalesReturnOrderForm, PurchaseReturnDetailFormSet, SalesReturnDetailFormSet
)
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate

# Helper to check permissions
def can_manage_orders(user):
    # Salesperson can insert/update/modify bills in Purchase Order and Sales Order interfaces
    return user.position in ['sales', 'manager', 'purchaser']

def can_manage_returns(user):
    # Only manager or superuser can manage returns
    return user.is_superuser or user.position == 'manager'

def can_view_finance_data(user):
    # Finance can view Purchase Order, Sales Order, Customer and Supplier
    return user.position in ['finance', 'manager']

@login_required
def purchase_list(request):
    """采购订单列表视图"""
    queryset = PurchaseOrder.objects.select_related('supplier', 'employee').prefetch_related('details__medicine').all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(supplier__name__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(details__medicine__common_name__icontains=search_query)
        ).distinct()
    orders = queryset.order_by('-order_date')
    
    context = {
        'orders': orders,
        'search_query': search_query,
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
    queryset = SalesOrder.objects.select_related('customer', 'employee').prefetch_related('details__inventory__medicine').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(customer__name__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(details__inventory__medicine__common_name__icontains=search_query)
        ).distinct()

    orders = queryset.order_by('-order_date')
    
    context = {
        'orders': orders,
        'search_query': search_query,
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
    try:
        days = int(request.GET.get('days', 30))
    except Exception:
        days = 30
    if days not in [7, 30, 90]:
        days = 30
    since = timezone.now() - timedelta(days=days)
    
    purchase_stats = PurchaseOrder.objects.filter(order_date__gte=since, status='approved').aggregate(
        total_orders=Count('id'),
        total_amount=Sum('total_amount')
    )
    
    sales_stats = SalesOrder.objects.filter(order_date__gte=since, status='approved').aggregate(
        total_orders=Count('id'),
        total_amount=Sum('total_amount')
    )
    
    profit = (sales_stats['total_amount'] or 0) - (purchase_stats['total_amount'] or 0)
    
    purchase_daily_qs = (
        PurchaseOrder.objects.filter(order_date__gte=since, status='approved')
        .annotate(d=TruncDate('order_date'))
        .values('d')
        .annotate(amount=Sum('total_amount'))
        .order_by('d')
    )
    sales_daily_qs = (
        SalesOrder.objects.filter(order_date__gte=since, status='approved')
        .annotate(d=TruncDate('order_date'))
        .values('d')
        .annotate(amount=Sum('total_amount'))
        .order_by('d')
    )
    purchase_daily = [{'date': x['d'], 'amount': x['amount'] or 0} for x in purchase_daily_qs]
    sales_daily = [{'date': x['d'], 'amount': x['amount'] or 0} for x in sales_daily_qs]
    max_amount = max([*(y['amount'] for y in purchase_daily), *(y['amount'] for y in sales_daily), 1])
    for x in purchase_daily:
        x['pct'] = int((x['amount'] / max_amount) * 100)
    for x in sales_daily:
        x['pct'] = int((x['amount'] / max_amount) * 100)
    
    # 最近的采购和销售记录（各取前5条）
    recent_purchases = PurchaseOrder.objects.select_related('supplier').filter(status='approved').order_by('-order_date')[:5]
    recent_sales = SalesOrder.objects.select_related('customer').filter(status='approved').order_by('-order_date')[:5]

    context = {
        'purchase_stats': purchase_stats,
        'sales_stats': sales_stats,
        'profit': profit,
        'period': f'最近{days}天',
        'days': days,
        'purchase_daily': purchase_daily,
        'sales_daily': sales_daily,
        'recent_purchases': recent_purchases,
        'recent_sales': recent_sales,
    }
    return render(request, 'biz/finance_report.html', context)

# ==========================================
# 采购退货视图
# ==========================================
@login_required
def purchase_return_list(request):
    if not can_manage_returns(request.user):
        messages.error(request, '无权限访问采购退货模块')
        return redirect('index')
        
    queryset = PurchaseReturnOrder.objects.select_related('supplier', 'employee').prefetch_related('details__inventory__medicine').all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(supplier__name__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(details__inventory__medicine__common_name__icontains=search_query)
        ).distinct()
    orders = queryset.order_by('-return_date')
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'can_edit': True
    }
    return render(request, 'biz/purchase_return_list.html', context)

@login_required
def purchase_return_create(request):
    if not can_manage_returns(request.user):
        messages.error(request, '无权限创建采购退货单')
        return redirect('purchase_return_list')
    
    if request.method == 'POST':
        form = PurchaseReturnOrderForm(request.POST)
        formset = PurchaseReturnDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.employee = request.user
            order.save()
            formset.instance = order
            formset.save()
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '采购退货单已创建')
            return redirect('purchase_return_list')
    else:
        form = PurchaseReturnOrderForm()
        formset = PurchaseReturnDetailFormSet()
    return render(request, 'biz/purchase_return_form.html', {'form': form, 'formset': formset, 'title': '新建采购退货单'})

@login_required
def purchase_return_edit(request, pk):
    if not can_manage_returns(request.user):
        messages.error(request, '无权限修改采购退货单')
        return redirect('purchase_return_list')
        
    order = get_object_or_404(PurchaseReturnOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseReturnOrderForm(request.POST, instance=order)
        formset = PurchaseReturnDetailFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '采购退货单已更新')
            return redirect('purchase_return_list')
    else:
        form = PurchaseReturnOrderForm(instance=order)
        formset = PurchaseReturnDetailFormSet(instance=order)
    return render(request, 'biz/purchase_return_form.html', {'form': form, 'formset': formset, 'title': '编辑采购退货单', 'order': order})

# ==========================================
# 销售退货视图
# ==========================================
@login_required
def sales_return_list(request):
    if not can_manage_returns(request.user):
        messages.error(request, '无权限访问销售退货模块')
        return redirect('index')
        
    queryset = SalesReturnOrder.objects.select_related('customer', 'employee').prefetch_related('details__inventory__medicine').all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(customer__name__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(details__inventory__medicine__common_name__icontains=search_query)
        ).distinct()
    orders = queryset.order_by('-return_date')
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'can_edit': True
    }
    return render(request, 'biz/sales_return_list.html', context)

@login_required
def sales_return_create(request):
    if not can_manage_returns(request.user):
        messages.error(request, '无权限创建销售退货单')
        return redirect('sales_return_list')
    
    if request.method == 'POST':
        form = SalesReturnOrderForm(request.POST)
        formset = SalesReturnDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.employee = request.user
            order.save()
            formset.instance = order
            formset.save()
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '销售退货单已创建')
            return redirect('sales_return_list')
    else:
        form = SalesReturnOrderForm()
        formset = SalesReturnDetailFormSet()
    return render(request, 'biz/sales_return_form.html', {'form': form, 'formset': formset, 'title': '新建销售退货单'})

@login_required
def sales_return_edit(request, pk):
    if not can_manage_returns(request.user):
        messages.error(request, '无权限修改销售退货单')
        return redirect('sales_return_list')
        
    order = get_object_or_404(SalesReturnOrder, pk=pk)
    if request.method == 'POST':
        form = SalesReturnOrderForm(request.POST, instance=order)
        formset = SalesReturnDetailFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            order.total_amount = sum(item.total_amount for item in order.details.all())
            order.save()
            messages.success(request, '销售退货单已更新')
            return redirect('sales_return_list')
    else:
        form = SalesReturnOrderForm(instance=order)
        formset = SalesReturnDetailFormSet(instance=order)
    return render(request, 'biz/sales_return_form.html', {'form': form, 'formset': formset, 'title': '编辑销售退货单', 'order': order})

