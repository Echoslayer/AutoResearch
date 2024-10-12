from django.urls import path
from .views import PromptGeneratorView

urlpatterns = [
    path('prompt_generator/', PromptGeneratorView.as_view(), name='generate_prompt'),
]
