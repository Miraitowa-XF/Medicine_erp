from django.db import models
from django.contrib.auth.models import AbstractUser

class Employee(AbstractUser):
    POSITION_CHOICES = (
        ('manager', '经理 - 全权管理'),
        ('purchaser', '采购员 - 进货管理'),
        ('warehouse', '库管员 - 库存盘点'),
        ('sales', '销售员 - 销售出库'),
        ('finance', '财务 - 统计报表'),
    )
    
    real_name = models.CharField(max_length=20, verbose_name='真实姓名', default='')
    mobile = models.CharField(max_length=11, verbose_name='手机号', blank=True, null=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='sales', verbose_name='职位')

    class Meta:
        verbose_name = '员工'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.real_name if self.real_name else self.username

    def save(self, *args, **kwargs):
        # 只要是员工，默认都能登录后台（is_staff=True）
        # 具体的权限（能不能看某个表）由 Django 的 Group 或后续业务逻辑控制
        self.is_staff = True
        super().save(*args, **kwargs)
