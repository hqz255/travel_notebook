from django.urls import path
from explore_world import views

app_name = 'explore_world'

urlpatterns = [
    path('', views.explore_world, name='explore_world'),
]
