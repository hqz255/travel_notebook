import os

from django.conf import settings
from django.db import models


class ArticleCategory(models.Model):
    """文章分类表 — 可扩展的分类体系"""
    name = models.CharField(max_length=50, unique=True, verbose_name='分类名称')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='URL 标识')
    display_order = models.IntegerField(default=0, verbose_name='排序权重')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'article_category'
        verbose_name = '文章分类'
        verbose_name_plural = verbose_name
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.name


class Article(models.Model):
    """文章表"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
    )

    title = models.CharField(max_length=200, verbose_name='文章标题')
    content = models.TextField(verbose_name='文章内容')
    author = models.ForeignKey(
        'register.User',
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='作者',
    )
    categories = models.ManyToManyField(
        ArticleCategory,
        related_name='articles',
        verbose_name='文章分类',
    )
    images = models.JSONField(default=list, blank=True, verbose_name='图片列表')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='发布状态',
    )
    views_count = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'article'
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def _image_exists(self, path):
        """检查图片文件是否真实存在于 media 目录"""
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        return os.path.isfile(full_path)

    @property
    def image_urls(self):
        """返回图片的完整 URL 路径列表（仅返回确实存在的文件）"""
        if not self.images:
            return []
        return [f'/media/{path}' for path in self.images if self._image_exists(path)]

    @property
    def all_image_urls(self):
        """返回所有图片 URL（包括不存在的），用于调试"""
        if not self.images:
            return []
        return [f'/media/{path}' for path in self.images]

    @property
    def category_names(self):
        """返回所有分类名称列表"""
        return list(self.categories.values_list('name', flat=True))


class Comment(models.Model):
    """文章评论表"""
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属文章',
    )
    author = models.ForeignKey(
        'register.User',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者',
    )
    content = models.TextField(verbose_name='评论内容')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'article_comment'
        verbose_name = '文章评论'
        verbose_name_plural = verbose_name
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['article', 'created_at']),
        ]

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'
