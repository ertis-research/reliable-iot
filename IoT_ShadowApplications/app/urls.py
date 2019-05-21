from my_app import views
from django.urls import path

urlpatterns = [
    path('interest/', views.interest),
    path('action/', views.action),
]

