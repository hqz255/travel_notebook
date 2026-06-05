from django.contrib import admin
from register.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'superuser', 'aactive', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('superuser', 'aactive', 'created_at')
