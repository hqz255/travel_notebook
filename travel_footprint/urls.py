from django.urls import path
from travel_footprint import views

app_name = 'travel_footprint'

urlpatterns = [
    path('', views.travel_footprint, name='travel_footprint'),
]
