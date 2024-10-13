from django.urls import path
from . import views

urlpatterns = [
    path('outline_agent/', views.generate_outline, name='generate_outline'),
]
