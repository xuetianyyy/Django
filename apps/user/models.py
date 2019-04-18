from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel
# Create your models here.


class User(AbstractUser, BaseModel):
    '''用户模型类'''

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AddressManage(models.Manager):
    """ 自定义一个模型管理器类 """

    def get_default_addr(self, user):
        """
        获取用户默认收货地址
        :user: 必须是一个QuerySet对象
        :return: 如果有默认收货地址, 则返回该查询对象QuerySet, 否则返回None
        """
        try:
            address = self.get(user=user, is_default=True)
        except Address.DoesNotExist:
            # 不存在默认收货地址
            address = None
        return address


class Address(BaseModel):
    '''地址模型类'''
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, verbose_name='所属账户', )
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    # 使用自定义模型管理器类
    objects = AddressManage()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name
