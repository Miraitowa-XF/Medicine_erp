"""
URL configuration for medicine_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users import views as user_views
from base import views as base_views
from biz import views as biz_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.index, name='index'),
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('change-password/', user_views.change_password, name='change_password'),
    path('employees/', user_views.employee_list, name='employee_list'),
    path('employees/<int:pk>/edit/', user_views.employee_edit, name='employee_edit'),
    path('employees/new/', user_views.employee_create, name='employee_create'),
    path('employees/<int:pk>/delete/', user_views.employee_delete, name='employee_delete'),
    path('employees/<int:pk>/password/', user_views.employee_password, name='employee_password'),
    
    # 业务模块路由
    path('medicine/', base_views.medicine_list, name='medicine_list'),
    path('inventory/<int:pk>/adjust/', base_views.inventory_adjust, name='inventory_adjust'),
    path('inventory/new/', base_views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/edit/', base_views.inventory_edit, name='inventory_edit'),
    path('medicine-info/', base_views.medicine_info_list, name='medicine_info_list'),
    path('customer/', base_views.customer_list, name='customer_list'),
    path('supplier/', base_views.supplier_list, name='supplier_list'),
    path('purchase/', biz_views.purchase_list, name='purchase_list'),
    path('purchase/new/', biz_views.purchase_create, name='purchase_create'),
    path('purchase/<int:pk>/edit/', biz_views.purchase_edit, name='purchase_edit'),
    path('sales/', biz_views.sales_list, name='sales_list'),
    path('sales/new/', biz_views.sales_create, name='sales_create'),
    path('sales/<int:pk>/edit/', biz_views.sales_edit, name='sales_edit'),
    path('finance-report/', biz_views.finance_report, name='finance_report'),
    path('purchase-return/', biz_views.purchase_return_list, name='purchase_return_list'),
    path('purchase-return/new/', biz_views.purchase_return_create, name='purchase_return_create'),
    path('purchase-return/<int:pk>/edit/', biz_views.purchase_return_edit, name='purchase_return_edit'),
    path('sales-return/', biz_views.sales_return_list, name='sales_return_list'),
    path('sales-return/new/', biz_views.sales_return_create, name='sales_return_create'),
    path('sales-return/<int:pk>/edit/', biz_views.sales_return_edit, name='sales_return_edit'),
]
