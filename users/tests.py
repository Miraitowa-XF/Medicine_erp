from django.test import TestCase
from django.contrib.auth.models import Group
from .models import Employee

class EmployeeModelTests(TestCase):
    def setUp(self):
        """测试数据初始化"""
        self.employee_data = {
            'username': 'testuser',
            'password': 'password123',
            'real_name': '测试员工',
            'position': 'sales',
            'mobile': '13800138000'
        }

    def test_create_employee(self):
        """测试创建员工基本信息"""
        employee = Employee.objects.create_user(**self.employee_data)
        self.assertEqual(employee.real_name, '测试员工')
        self.assertEqual(employee.position, 'sales')
        self.assertEqual(employee.mobile, '13800138000')
        # 验证默认值
        self.assertEqual(employee.sex, 'M')
        self.assertEqual(employee.permission_level, 1)

    def test_employee_str(self):
        """测试模型的字符串表示"""
        employee = Employee.objects.create_user(**self.employee_data)
        self.assertEqual(str(employee), '测试员工')
        
        # 测试没有真实姓名时显示用户名
        employee.real_name = ''
        employee.save()
        self.assertEqual(str(employee), 'testuser')

    def test_is_staff_auto_set(self):
        """测试保存时是否自动设置 is_staff=True"""
        employee = Employee.objects.create_user(**self.employee_data)
        # create_user 内部会调用 save()
        self.assertTrue(employee.is_staff)

    def test_group_assignment_on_creation(self):
        """测试创建员工时是否自动分配到对应职位的组"""
        employee = Employee.objects.create_user(**self.employee_data)
        
        # 验证组是否存在
        group_exists = Group.objects.filter(name='sales').exists()
        self.assertTrue(group_exists, "应该自动创建 'sales' 组")
        
        # 验证员工是否在组内
        sales_group = Group.objects.get(name='sales')
        self.assertIn(sales_group, employee.groups.all(), "员工应该被分配到 'sales' 组")

    def test_group_change_on_position_update(self):
        """测试修改职位时，用户组是否自动变更"""
        employee = Employee.objects.create_user(**self.employee_data)
        sales_group = Group.objects.get(name='sales')
        
        # 修改职位为 'manager'
        employee.position = 'manager'
        employee.save()
        
        # 验证新组是否存在
        manager_group_exists = Group.objects.filter(name='manager').exists()
        self.assertTrue(manager_group_exists, "应该自动创建 'manager' 组")
        
        manager_group = Group.objects.get(name='manager')
        
        # 验证员工加入了新组
        self.assertIn(manager_group, employee.groups.all(), "员工应该被分配到 'manager' 组")
        
        # 验证员工退出了旧组
        self.assertNotIn(sales_group, employee.groups.all(), "员工应该从 'sales' 组移除")
