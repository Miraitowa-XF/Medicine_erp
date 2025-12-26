from django.db import models

# --- 抽象基类 (不会在数据库建表，仅供继承) ---
class AddressInfo(models.Model):
    # 三级行政区划
    province = models.CharField("省份", max_length=50)
    city = models.CharField("城市", max_length=50)
    district = models.CharField("区县", max_length=50)
    # 具体地址
    street = models.CharField("街道/乡镇", max_length=200, help_text="包含街道或乡镇信息")
    detail_address = models.CharField("详细地址", max_length=200, help_text="如:10号院3单元502室")
    # 邮政编码
    zip_code = models.CharField("邮政编码", max_length=10)

    class Meta:
        abstract = True


    @property
    def full_address(self):
        """获取完整地址，自动过滤空值"""
        parts = [
            self.province,
            self.city,
            self.district,
            self.street,
            self.detail_address
        ]
        # 过滤空值
        non_empty_parts = [part for part in parts if part]
        return ''.join(non_empty_parts)
    
# --- 强实体 ---

class Medicine(models.Model):
    """药品信息"""
    # MedicineID 由 Django 自动生成 id
    common_name = models.CharField("通用名", max_length=100)
    specification = models.CharField("规格", max_length=50)
    manufacturer = models.CharField("生产厂家", max_length=100)
    # unit = models.CharField("单位", max_length=10)
    approval_number = models.CharField("批准文号", max_length=50, unique=True, help_text="国药准字")
    
    buy_price = models.DecimalField("指导进价", max_digits=10, decimal_places=2)
    sell_price = models.DecimalField("指导售价", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "药品信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.common_name} - {self.specification}"
    

class Supplier(AddressInfo):
    """供应商 (继承地址信息)"""
    name = models.CharField("供应商名称", max_length=100)
    contact_person = models.CharField("联系人", max_length=50)
    license_no = models.CharField("经营许可证号", max_length=50)

    # 删除旧的简单处理的多值属性
    # phone = models.CharField("联系电话", max_length=50, help_text="多个电话用逗号分隔")

    class Meta:
        verbose_name = "供应商"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
    
# 创建一个新的模型 SupplierPhone，并通过外键关联到 Supplier
class SupplierPhone(models.Model):
    """
    供应商联系电话表 (解决多值属性)
    一个供应商可以有多个电话
    """
    # 电话类型选项
    TYPE_CHOICES = [
        ('mobile', '手机'),
        ('office', '座机'),
        ('fax', '传真'),
        ('other', '其他'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='phones', verbose_name="所属供应商")
    number = models.CharField("电话号码", max_length=20)
    type = models.CharField("类型", max_length=10, choices=TYPE_CHOICES, default='mobile')
    note = models.CharField("备注", max_length=50, blank=True, help_text="如：紧急联系人")

    class Meta:
        verbose_name = "联系电话"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.get_type_display()}: {self.number}"
    

class Customer(AddressInfo):
    """客户 (继承地址信息)"""
    name = models.CharField("客户姓名/药店名", max_length=100)
    type = models.CharField("类型", max_length=20, choices=[('wholesale', '批发'), ('retail', '零售')])
    phone = models.CharField("联系电话", max_length=20)

    class Meta:
        verbose_name = "客户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
    

# --- 核心实体 (Inventory) ---

class Inventory(models.Model):
    """库存表 (强实体设计，代理主键 InventoryID)"""
    # 对应 ER 图：Has_Batch 关系 (指向 Medicine)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, verbose_name="药品")
    
    batch_number = models.CharField("生产批号", max_length=50)
    expiry_date = models.DateField("有效期至")
    quantity = models.PositiveIntegerField("当前数量", default=0)
    # 库位可选，暂时先注释
    # warehouse_location = models.CharField("库位", max_length=50, blank=True)

    class Meta:
        # 业务约束：同一种药+同一个批号，只能有一条库存记录
        unique_together = ('medicine', 'batch_number')
        verbose_name = "库存记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.medicine.common_name} [{self.batch_number}] 余: {self.quantity}"