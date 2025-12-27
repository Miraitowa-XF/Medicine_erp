from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib import messages
from django import forms
from .models import Employee

# 登录视图
def login_view(request):
    # 如果用户已登录，重定向到首页
    if request.user.is_authenticated:
        return redirect('index')
    # 处理POST请求
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': '用户名或密码错误'})
    # 处理GET请求
    else:
        return render(request, 'login.html')
# 注销视图
def logout_view(request):
    logout(request)
    return redirect('login')
# 首页视图
@login_required(login_url='login')
def index(request):
    return render(request, 'index.html')
# 修改密码视图
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '密码修改成功！')
            return redirect('index')
        else:
            messages.error(request, '请修正下面的错误。')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })

# 检查用户是否为管理员或经理
def _is_manager(user):
    return user.is_superuser or getattr(user, 'position', '') == 'manager'

# 员工表单
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['username', 'real_name', 'email', 'mobile', 'position', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'readonly': True}),
        }

# 员工创建表单
class EmployeeCreateForm(forms.ModelForm):
    password1 = forms.CharField(label='初始密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput)
    class Meta:
        model = Employee
        fields = ['username', 'real_name', 'email', 'mobile', 'position', 'is_active']
    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 != p2:
            self.add_error('password2', '两次输入的密码不一致')
        return cleaned
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

# 员工列表视图
@login_required(login_url='login')
def employee_list(request):
    if not _is_manager(request.user):
        messages.error(request, '无权限访问员工管理')
        return redirect('index')
    q = request.GET.get('q', '').strip()
    employees = Employee.objects.all().order_by('username')
    if q:
        employees = employees.filter(username__icontains=q)
    return render(request, 'users/employee_list.html', {'employees': employees, 'q': q})

# 员工编辑视图
@login_required(login_url='login')
def employee_edit(request, pk):
    if not _is_manager(request.user):
        messages.error(request, '无权限编辑员工信息')
        return redirect('index')
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, '员工信息已更新')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'users/employee_edit.html', {'form': form, 'emp': emp})

# 员工创建视图
@login_required(login_url='login')
def employee_create(request):
    if not _is_manager(request.user):
        messages.error(request, '无权限新增员工')
        return redirect('index')
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '员工已创建')
            return redirect('employee_list')
    else:
        form = EmployeeCreateForm()
    return render(request, 'users/employee_create.html', {'form': form})

# 员工删除视图
@login_required(login_url='login')
def employee_delete(request, pk):
    if not _is_manager(request.user):
        messages.error(request, '无权限删除员工')
        return redirect('index')
    emp = get_object_or_404(Employee, pk=pk)
    if emp.id == request.user.id:
        messages.error(request, '不可删除当前登录账户')
        return redirect('employee_list')
    if request.method == 'POST':
        emp.delete()
        messages.success(request, '员工已删除')
        return redirect('employee_list')
    messages.error(request, '非法请求')
    return redirect('employee_list')

# 员工密码重置视图
@login_required(login_url='login')
def employee_password(request, pk):
    if not _is_manager(request.user):
        messages.error(request, '无权限重置员工密码')
        return redirect('index')
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = SetPasswordForm(emp, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '员工密码已重置')
            return redirect('employee_list')
    else:
        form = SetPasswordForm(emp)
    return render(request, 'users/employee_password.html', {'form': form, 'emp': emp})
