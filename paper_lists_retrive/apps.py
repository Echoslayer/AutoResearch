from django.apps import AppConfig
from .services.Supabase_service import Supabase


class PaperListsRetriveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paper_lists_retrive'

    def ready(self):
        Supabase.initialize()
