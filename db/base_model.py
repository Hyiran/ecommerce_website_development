"""抽象模型基类"""
'''
@Time    : 2018/3/9 上午8:14
@Author  : scrappy_zhang
@File    : base_model.py
'''

from django.db import models


class BaseModel(models.Model):
    """抽象模型基类"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')

    class Meta:
        # 指定这个类是一个抽象模型类
        abstract = True
