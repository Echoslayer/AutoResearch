from django.apps import AppConfig


class PromptGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prompt_generator'

    def ready(self):
        # Import and register any signal handlers or perform any app-specific initialization
        pass
