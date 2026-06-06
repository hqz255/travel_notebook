from django.urls import path
from explore_world import views

app_name = 'explore_world'

urlpatterns = [
    path('', views.explore_world, name='explore_world'),
    path('<int:article_id>/', views.article_detail, name='article_detail'),
    path('<int:article_id>/comment/', views.post_comment, name='post_comment'),
    path('<int:article_id>/comments/', views.get_comments, name='get_comments'),
]
