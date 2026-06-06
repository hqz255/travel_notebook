from django.contrib import admin
from record_memories.models import Article, ArticleCategory


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_order', 'is_active', 'created_at']
    list_editable = ['display_order', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'category_names_display', 'views_count', 'created_at']
    list_filter = ['status', 'categories', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    filter_horizontal = ['categories']
    readonly_fields = ['views_count', 'created_at', 'updated_at']

    def category_names_display(self, obj):
        return '、'.join(obj.category_names)
    category_names_display.short_description = '分类'
