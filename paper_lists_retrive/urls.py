from django.urls import path
from .views import SupabaseSearchAPIView

urlpatterns = [
    path('paper_retrieve/', SupabaseSearchAPIView.as_view(), name='supabase-search'),
]
