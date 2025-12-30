from django.test import TestCase
from django.db.utils import IntegrityError
from django.utils import timezone
from .models import Medicine, Supplier, SupplierPhone, Customer, Inventory
from datetime import timedelta

class BaseModelTests(TestCase):
    def setUp(self):
        # 初始化测试数据
        self.medicine_data = {
            'common_name': '阿莫西林胶囊',
            'specification': '0.25g*24粒',
            'manufacturer': '某某制药厂',
            'approval_number': '国药准字H12345678',
            'buy_price': 10.00,
            'sell_price': 25.00
        }
        
        self.supplier_data = {
            'name': '测试供应商',
            'contact_person': '张三',
            'license_no': 'JY123456789',
            'province': '北京市',
            'city': '北京市',
            'district': '朝阳区',
            'street': '某某街道',
            'detail_address': '1号院',
            'zip_code': '100000'
        }

        self.customer_data = {
            'name': '测试大药房',
            'type': 'retail',
            'phone': '010-12345678',
            'province': '上海市',
            'city': '上海市',
            'district': '浦东新区',
            'street': '某某路',
            'detail_address': '114514号',
            'zip_code': '200000'
        }

    def test_create_medicine(self):
        """测试创建药品信息"""
        medicine = Medicine.objects.create(**self.medicine_data)
        self.assertEqual(medicine.common_name, '阿莫西林胶囊')
        self.assertEqual(str(medicine), '阿莫西林胶囊 - 0.25g*24粒')

    def test_create_supplier_and_phone(self):
        """测试创建供应商及其联系电话"""
        supplier = Supplier.objects.create(**self.supplier_data)
        self.assertEqual(supplier.name, '测试供应商')
        # 测试地址属性
        self.assertEqual(supplier.full_address, '北京市北京市朝阳区某某街道1号院')

        # 测试添加电话
        phone = SupplierPhone.objects.create(
            supplier=supplier,
            number='13800138000',
            type='mobile',
            note='紧急联系'
        )
        self.assertEqual(phone.supplier, supplier)
        self.assertEqual(str(phone), '手机: 13800138000')

    def test_create_customer(self):
        """测试创建客户信息"""
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(customer.name, '测试大药房')
        self.assertEqual(customer.type, 'retail')
        self.assertEqual(customer.full_address, '上海市上海市浦东新区某某路114514号')

    def test_create_inventory(self):
        """测试创建库存记录"""
        medicine = Medicine.objects.create(**self.medicine_data)
        inventory = Inventory.objects.create(
            medicine=medicine,
            batch_number='BATCH20231230',
            expiry_date=timezone.now().date() + timedelta(days=365),
            quantity=100
        )
        self.assertEqual(inventory.quantity, 100)
        self.assertTrue(str(inventory).startswith('阿莫西林胶囊'))

    def test_inventory_unique_constraint(self):
        """测试库存的唯一性约束 (同药品同批号)"""
        medicine = Medicine.objects.create(**self.medicine_data)
        batch = 'BATCH_UNIQUE'
        expiry = timezone.now().date() + timedelta(days=365)
        
        # 创建第一条记录
        Inventory.objects.create(
            medicine=medicine,
            batch_number=batch,
            expiry_date=expiry,
            quantity=50
        )

        # 尝试创建第二条相同的记录，应该抛出 IntegrityError
        with self.assertRaises(IntegrityError):
            Inventory.objects.create(
                medicine=medicine,
                batch_number=batch,
                expiry_date=expiry,
                quantity=20
            )