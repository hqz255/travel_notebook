from django.db import models


class User(models.Model):
    """用户表"""
    username = models.CharField(max_length=20, unique=True, verbose_name='用户名')
    email = models.EmailField(max_length=254, unique=True, verbose_name='邮箱')
    password = models.CharField(max_length=256, verbose_name='密码')
    superuser = models.BooleanField(default=False, verbose_name='超级用户')
    aactive = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
