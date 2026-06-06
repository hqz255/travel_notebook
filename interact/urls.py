from django.urls import path
from interact import views

app_name = 'interact'

urlpatterns = [
    path('', views.interact, name='interact'),
]
