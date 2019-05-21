from django.urls import path
from my_register.register import views


urlpatterns = [
    path('register/', views.register, name='register'),
]
