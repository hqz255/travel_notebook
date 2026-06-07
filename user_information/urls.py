from django.urls import path
from user_information import views

app_name = 'user_information'

urlpatterns = [
    path('pubs/', views.user_pub, name='user_pub'),
    path('setting/', views.user_setting, name='user_setting'),
]
