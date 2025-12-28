from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group  # 引入原生 Group

class Employee(AbstractUser):
    POSITION_CHOICES = (
        ('manager', '经理 - 全权管理'),
        ('purchaser', '采购员 - 进货管理'),
        ('warehouse', '库管员 - 库存盘点'),
        ('sales', '销售员 - 销售出库'),
        ('finance', '财务 - 统计报表'),
    )
    
    real_name = models.CharField(max_length=20, verbose_name='真实姓名', default='')
    sex = models.CharField("性别", max_length=10, choices=[('M', '男'), ('F', '女')], default='M')
    age = models.PositiveIntegerField("年龄", null=True, blank=True)
    mobile = models.CharField(max_length=11, verbose_name='手机号', blank=True, null=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='sales', verbose_name='职位')
    # 权限等级 (简单实现，复杂权限可用 Django Group)
    permission_level = models.IntegerField("权限等级", default=1, help_text="1:普通, 5:管理, 9:系统")

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

        # === 自动权限组管理 ===
        if self.position:
            # 1. 获取或创建当前职位对应的组 (使用 position 的 key 作为组名)
            group, _ = Group.objects.get_or_create(name=self.position)
            # 确保用户在当前职位的组中
            self.groups.add(group)

            # 2. 移除用户不再属于的职位组 (处理职位变更的情况)
            for code, _ in self.POSITION_CHOICES:
                if code != self.position:
                    try:
                        old_group = Group.objects.get(name=code)
                        if old_group in self.groups.all():
                            self.groups.remove(old_group)
                    except Group.DoesNotExist:
                        pass


class ProxyGroup(Group):
    """
    代理组模型：
    作用仅仅是为了把 Group 显示在 'users' 应用下，
    而不使用原本的 'Authentication and Authorization' 分类
    """
    class Meta:
        proxy = True  # 关键：设置为代理模型，不会在数据库创建新表
        verbose_name = "职位/用户组"
        verbose_name_plural = verbose_name