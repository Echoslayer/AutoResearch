from django.urls import path
from .views import ChatAPIView, BatchGenerateAPIView

urlpatterns = [
    path('generate/', ChatAPIView.as_view(), name='chat'),
    path('batch-generate/', BatchGenerateAPIView.as_view(), name='batch-generate'),
]
