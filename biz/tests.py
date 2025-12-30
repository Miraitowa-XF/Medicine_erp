from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from base.models import Supplier, Medicine, Customer, Inventory
from biz.models import (
    PurchaseOrder, PurchaseDetail,
    SalesOrder, SalesDetail,
    SalesReturnOrder, SalesReturnDetail,
    PurchaseReturnOrder, PurchaseReturnDetail
)
from datetime import timedelta

User = get_user_model()

class BizModelTests(TestCase):
    def setUp(self):
        # 创建用户
        self.user = User.objects.create_user(username='testuser', password='password')

        # 创建供应商
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            license_no='1234567890',
            province='Test Province',
            city='Test City',
            district='Test District',
            street='Test Street',
            detail_address='Test Address',
            zip_code='100000'
        )

        # 创建药品
        self.medicine = Medicine.objects.create(
            common_name='Test Medicine',
            specification='10mg*10',
            manufacturer='Test Manufacturer',
            approval_number='H12345678',
            buy_price=10.00,
            sell_price=20.00
        )

        # 创建客户
        self.customer = Customer.objects.create(
            name='Test Customer',
            type='retail',
            phone='13800138000',
            province='Test Province',
            city='Test City',
            district='Test District',
            street='Test Street',
            detail_address='Test Address',
            zip_code='100000'
        )

        # 创建库存
        self.inventory = Inventory.objects.create(
            medicine=self.medicine,
            batch_number='BATCH001',
            expiry_date=timezone.now().date() + timedelta(days=365),
            quantity=100
        )

    def test_purchase_order_creation(self):
        """测试创建进货单和进货明细"""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            employee=self.user,
            status='pending'
        )
        self.assertEqual(po.status, 'pending')
        self.assertEqual(po.supplier, self.supplier)

        detail = PurchaseDetail.objects.create(
            order=po,
            medicine=self.medicine,
            batch_number='BATCH002',
            produce_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            quantity=10,
            unit_price=10.00
        )
        
        # 检查总金额计算是否正确
        self.assertEqual(detail.total_amount, 100.00)
        self.assertEqual(str(detail), f"{self.medicine} (BATCH002)")

    def test_sales_order_creation(self):
        """测试创建销售单和销售明细"""
        so = SalesOrder.objects.create(
            customer=self.customer,
            employee=self.user,
            status='pending'
        )
        self.assertEqual(so.status, 'pending')

        detail = SalesDetail.objects.create(
            order=so,
            inventory=self.inventory,
            quantity=5,
            actual_price=20.00
        )

        # 检查总金额计算
        self.assertEqual(detail.total_amount, 100.00)
        # 检查批号快照
        self.assertEqual(detail.batch_number_snapshot, 'BATCH001')
        self.assertEqual(str(detail), f"Out: {self.medicine} * 5")

    def test_sales_return_order_creation(self):
        """测试创建销售退货单和销售退货明细"""
        sro = SalesReturnOrder.objects.create(
            customer=self.customer,
            employee=self.user,
            status='pending'
        )
        
        detail = SalesReturnDetail.objects.create(
            order=sro,
            inventory=self.inventory,
            quantity=2,
            refund_price=20.00
        )

        self.assertEqual(detail.total_amount, 40.00)
        self.assertEqual(str(detail), f"Return: {self.medicine} * 2")

    def test_purchase_return_order_creation(self):
        """测试创建采购退货单和采购退货明细"""
        pro = PurchaseReturnOrder.objects.create(
            supplier=self.supplier,
            employee=self.user,
            status='pending'
        )

        detail = PurchaseReturnDetail.objects.create(
            order=pro,
            inventory=self.inventory,
            quantity=5,
            unit_price=10.00
        )

        self.assertEqual(detail.total_amount, 50.00)
        self.assertEqual(str(detail), f"Deduct: {self.medicine} * 5")