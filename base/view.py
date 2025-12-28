from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from .models import Inventory, Customer, Medicine
from django.utils import timezone
from datetime import timedelta, date
from django.db import IntegrityError

@login_required
def medicine_list(request):
    """药品库存列表视图"""
    # 获取所有库存记录，并预加载关联的 Medicine 数据以减少数据库查询
    inventory_items = Inventory.objects.select_related('medicine').all().order_by('medicine__common_name', 'expiry_date')
    
    # 简单的临期判断逻辑 (未来3个月内过期)
    today = timezone.now().date()
    warning_date = today + timedelta(days=90)
    
    for item in inventory_items:
        item.is_expiring_soon = item.expiry_date <= warning_date
        
    context = {
        'inventory_items': inventory_items,
    }
    return render(request, 'base/medicine_list.html', context)

# 客户列表视图
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    context = {
        'customers': customers,
    }
    return render(request, 'base/customer_list.html', context)

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
    if not request.user.has_perm('base.view_medicine'):
        messages.error(request, '无权限查看药品信息')
        return redirect('index')
    medicines = Medicine.objects.all().order_by('common_name', 'manufacturer')
    return render(request, 'base/medicine_info_list.html', {'medicines': medicines})
