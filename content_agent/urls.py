from django.urls import path
from . import views

urlpatterns = [
    path('content-generator/', views.generate_content, name='generate_content'),
]
