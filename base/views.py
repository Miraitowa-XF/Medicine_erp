from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import Inventory, Customer, Medicine, Supplier
from django.utils import timezone
from datetime import timedelta, date
from django.db import IntegrityError
from django.db.models import Q
from django.core.paginator import Paginator

@login_required
def medicine_list(request):
    """药品库存列表视图"""
    # 允许 warehouse, manager, sales 查看库存
    if not (request.user.has_perm('base.view_inventory') or request.user.position in ['warehouse', 'manager', 'sales']):
        messages.error(request, '无权限查看库存')
        return redirect('index')

    queryset = Inventory.objects.select_related('medicine')
    
    # 搜索参数
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(medicine__common_name__icontains=search_query) |
            Q(medicine__manufacturer__icontains=search_query) |
            Q(batch_number__icontains=search_query)
        )
    
    # 筛选参数
    min_quantity = request.GET.get('min_quantity')
    max_quantity = request.GET.get('max_quantity')
    if min_quantity:
        queryset = queryset.filter(quantity__gte=min_quantity)
    if max_quantity:
        queryset = queryset.filter(quantity__lte=max_quantity)
    
    expiry_start = request.GET.get('expiry_start')
    expiry_end = request.GET.get('expiry_end')
    if expiry_start:
        queryset = queryset.filter(expiry_date__gte=expiry_start)
    if expiry_end:
        queryset = queryset.filter(expiry_date__lte=expiry_end)
    
    # 分页
    paginator = Paginator(queryset.order_by('medicine__common_name', 'expiry_date'), 20)
    page_number = request.GET.get('page')
    inventory_items = paginator.get_page(page_number)
    
    # 简单的临期判断逻辑 (未来3个月内过期)
    today = timezone.now().date()
    warning_date = today + timedelta(days=90)
    
    for item in inventory_items:
        item.is_expiring_soon = item.expiry_date <= warning_date
        
    context = {
        'inventory_items': inventory_items,
        'search_query': search_query,
        'min_quantity': min_quantity,
        'max_quantity': max_quantity,
        'expiry_start': expiry_start,
        'expiry_end': expiry_end,
    }
    return render(request, 'base/medicine_list.html', context)

# 客户列表视图
@login_required
def customer_list(request):
    queryset = Customer.objects.all()
    
    # 搜索参数
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(province__icontains=search_query) |
            Q(city__icontains=search_query)
        )

    # 筛选类型
    type_filter = request.GET.get('type')
    if type_filter:
        queryset = queryset.filter(type=type_filter)

    context = {
        'customers': queryset.order_by('name'),
        'search_query': search_query,
        'type_filter': type_filter,
    }
    return render(request, 'base/customer_list.html', context)

# 客户表单
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'type', 'phone',
            'province', 'city', 'district',
            'street', 'detail_address', 'zip_code'
        ]

# 新增客户
@login_required
def customer_create(request):
    # 销售员、经理、财务(只读)
    # 假设 sales 和 manager 可以新增
    if request.user.position not in ['sales', 'manager'] and not request.user.is_superuser:
        messages.error(request, '无权限新增客户')
        return redirect('customer_list')
    
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '客户已新增')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'base/customer_form.html', {'form': form, 'is_edit': False})

# 编辑客户
@login_required
def customer_edit(request, pk):
    if request.user.position not in ['sales', 'manager'] and not request.user.is_superuser:
        messages.error(request, '无权限修改客户')
        return redirect('customer_list')
        
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, '客户信息已更新')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'base/customer_form.html', {'form': form, 'is_edit': True, 'customer': customer})

# 库存调整表单
class InventoryAdjustForm(forms.Form):
    delta = forms.IntegerField(label='调整数量')

# 库存新增/编辑表单 
class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['medicine', 'batch_number', 'expiry_date', 'quantity']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['expiry_date'].widget.attrs['min'] = date.today().isoformat()
        except Exception:
            pass

# 库存调整视图
@login_required
def inventory_adjust(request, pk):
    if not request.user.has_perm('base.change_inventory'):
        messages.error(request, '无权限调整库存')
        return redirect('medicine_list')
    item = get_object_or_404(Inventory.objects.select_related('medicine'), pk=pk)
    if request.method == 'POST':
        form = InventoryAdjustForm(request.POST)
        if form.is_valid():
            delta = form.cleaned_data['delta']
            new_qty = item.quantity + delta
            if new_qty < 0:
                messages.error(request, '调整后数量不能为负数')
            else:
                item.quantity = new_qty
                item.save()
                messages.success(request, '库存已更新')
                return redirect('medicine_list')
    else:
        form = InventoryAdjustForm()
    return render(request, 'base/inventory_adjust.html', {'item': item, 'form': form})

# 库存新增视图
@login_required
def inventory_create(request):
    if not request.user.has_perm('base.add_inventory'):
        messages.error(request, '无权限新增库存')
        return redirect('medicine_list')
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '库存批次已新增')
                return redirect('medicine_list')
            except IntegrityError:
                form.add_error('batch_number', '同药品批号已存在')
    else:
        form = InventoryForm()
    return render(request, 'base/inventory_form.html', {'form': form, 'is_edit': False})

# 库存编辑视图
@login_required
def inventory_edit(request, pk):
    if not request.user.has_perm('base.change_inventory'):
        messages.error(request, '无权限修改库存')
        return redirect('medicine_list')
    item = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '库存批次已更新')
                return redirect('medicine_list')
            except IntegrityError:
                form.add_error('batch_number', '同药品批号已存在')
    else:
        form = InventoryForm(instance=item)
    return render(request, 'base/inventory_form.html', {'form': form, 'is_edit': True, 'item': item})

# 药品信息列表视图
@login_required
def medicine_info_list(request):
    # 允许 sales, warehouse, purchaser, manager
    if not (request.user.has_perm('base.view_medicine') or request.user.position in ['sales', 'warehouse', 'purchaser', 'manager']):
        messages.error(request, '无权限查看药品信息')
        return redirect('index')
    
    queryset = Medicine.objects.all()
    
    # 搜索参数
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(common_name__icontains=search_query) |
            Q(specification__icontains=search_query) |
            Q(manufacturer__icontains=search_query) |
            Q(approval_number__icontains=search_query)
        )
    
    # 筛选参数
    min_buy_price = request.GET.get('min_buy_price')
    max_buy_price = request.GET.get('max_buy_price')
    if min_buy_price:
        queryset = queryset.filter(buy_price__gte=min_buy_price)
    if max_buy_price:
        queryset = queryset.filter(buy_price__lte=max_buy_price)
    
    min_sell_price = request.GET.get('min_sell_price')
    max_sell_price = request.GET.get('max_sell_price')
    if min_sell_price:
        queryset = queryset.filter(sell_price__gte=min_sell_price)
    if max_sell_price:
        queryset = queryset.filter(sell_price__lte=max_sell_price)
    
    # 分页
    paginator = Paginator(queryset.order_by('common_name', 'manufacturer'), 20)
    page_number = request.GET.get('page')
    medicines = paginator.get_page(page_number)
    
    context = {
        'medicines': medicines,
        'search_query': search_query,
        'min_buy_price': min_buy_price,
        'max_buy_price': max_buy_price,
        'min_sell_price': min_sell_price,
        'max_sell_price': max_sell_price,
    }
    return render(request, 'base/medicine_info_list.html', context)

# 药品新增表单
class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['common_name', 'specification', 'manufacturer', 'approval_number', 'buy_price', 'sell_price']

# 药品新增视图
@login_required
def medicine_create(request):
    if not request.user.has_perm('base.add_medicine'):
        messages.error(request, '无权限新增药品')
        return redirect('medicine_info_list')
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '药品信息已新增')
            return redirect('medicine_info_list')
    else:
        form = MedicineForm()
    return render(request, 'base/medicine_form.html', {'form': form})

# 供应商列表视图
@login_required
def supplier_list(request):
    queryset = Supplier.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(license_no__icontains=search_query) |
            Q(province__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    suppliers = queryset.order_by('name')
    context = {
        'suppliers': suppliers,
        'search_query': search_query,
    }
    return render(request, 'base/supplier_list.html', context)

# 供应商表单
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'license_no',
            'province', 'city', 'district',
            'street', 'detail_address', 'zip_code'
        ]

# 新增供应商
@login_required
def supplier_create(request):
    if not request.user.has_perm('base.add_supplier'):
        messages.error(request, '无权限新增供应商')
        return redirect('supplier_list')
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '供应商已新增')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'base/supplier_form.html', {'form': form, 'is_edit': False})

# 编辑供应商
@login_required
def supplier_edit(request, pk):
    if not request.user.has_perm('base.change_supplier'):
        messages.error(request, '无权限修改供应商')
        return redirect('supplier_list')
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, '供应商信息已更新')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'base/supplier_form.html', {'form': form, 'is_edit': True, 'supplier': supplier})