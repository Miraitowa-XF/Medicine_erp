import os
import django
import threading
import time
import random

# 1. 初始化 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_system.settings')
django.setup()

from biz.models import SalesOrder, SalesDetail
from base.models import Inventory, Customer, Medicine
from users.models import Employee

def create_test_data():
    """准备测试数据：确保有一个库存为 10 的商品"""
    print(">>> 正在准备测试数据...")
    
    # 获取或创建基础数据
    try:
        medicine = Medicine.objects.first()
        if not medicine:
            print("错误：请先在后台至少添加一种药品！")
            return None
            
        # 查找或创建库存，强制设为 10
        inventory, _ = Inventory.objects.get_or_create(
            medicine=medicine,
            batch_number='TEST-BATCH-001',
            defaults={'expiry_date': '2026-01-01', 'quantity': 10}
        )
        inventory.quantity = 10
        inventory.save()
        
        customer = Customer.objects.first() or Customer.objects.create(name="测试客户", city="Test", street="Test", zip_code="000")
        employee = Employee.objects.first() # 确保有一个员工
        
        print(f"    测试目标: {medicine.common_name} (ID: {inventory.id})")
        print(f"    初始库存: {inventory.quantity}")
        return inventory.id, customer, employee
        
    except Exception as e:
        print(f"数据准备失败: {e}")
        return None

def worker_buy(inventory_id, customer, employee, quantity, thread_name):
    """
    模拟一个线程尝试购买
    """
    try:
        # 模拟网络延迟
        time.sleep(random.uniform(0.1, 0.5))
        
        print(f"[{thread_name}] 正在创建订单，意图购买 {quantity} 个...")
        
        # 1. 创建订单 (Pending)
        order = SalesOrder.objects.create(
            customer=customer, 
            employee=employee, 
            status='pending'
        )
        
        # 2. 创建明细
        # 注意：这里必须重新获取 Inventory 实例，或者只传 ID，防止对象混用
        inv_obj = Inventory.objects.get(id=inventory_id)
        SalesDetail.objects.create(
            order=order, 
            inventory=inv_obj, 
            quantity=quantity, 
            actual_price=10
        )
        
        # 3. 尝试审核 (触发并发锁逻辑)
        print(f"[{thread_name}] ---> 点击审核！")
        order.status = 'approved'
        order.save() # 这里会触发 signals.py 里的逻辑
        
        print(f"[{thread_name}] ✅✅✅ 抢购成功！")
        
    except ValueError as e:
        # 捕获库存不足的错误
        print(f"[{thread_name}] ❌ 抢购失败 (预期内): {e}")
    except Exception as e:
        print(f"[{thread_name}] ❌ 发生未知错误: {e}")

if __name__ == "__main__":
    # 1. 准备数据
    data = create_test_data()
    if not data:
        exit()
    
    inv_id, cust, emp = data
    
    # 2. 模拟高并发场景
    # 库存 10 个。
    # 启动 5 个线程，每个买 3 个。总需求 15 个。
    # 预期结果：前 3 个线程成功 (消耗9个)，剩 1 个。第 4、5 个线程应该失败。
    
    threads = []
    print("\n>>> 开始并发测试 (5个线程，每人买3个，总库存10个)...\n")
    
    for i in range(5):
        t = threading.Thread(
            target=worker_buy, 
            args=(inv_id, cust, emp, 3, f"Thread-{i+1}")
        )
        threads.append(t)
        t.start()
        
    # 等待所有线程结束
    for t in threads:
        t.join()
        
    # 3. 验证结果
    final_inv = Inventory.objects.get(id=inv_id)
    print("\n" + "="*30)
    print(f"测试结束。")
    print(f"最终库存: {final_inv.quantity}")
    
    if final_inv.quantity >= 0:
        print("✅ 测试通过：库存没有变成负数！")
    else:
        print("❌ 测试失败：出现超卖 (库存为负)！")
    print("="*30)