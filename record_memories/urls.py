from django.urls import path
from record_memories import views

app_name = 'record_memories'

urlpatterns = [
    path('', views.wmmr, name='wmmr'),
]
