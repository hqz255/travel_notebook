from django.urls import path
from login import views

app_name = 'login'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('send-code/', views.send_login_code, name='send_login_code'),
]
