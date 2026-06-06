from django.urls import path
from register import views

app_name = 'register'

urlpatterns = [
    path('', views.register_view, name='register'),
    path('send-code/', views.send_verification_code, name='send_code'),
]
