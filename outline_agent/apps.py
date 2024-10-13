from django.apps import AppConfig
from outline_agent.services.outline_agent_service import OutlineWriter

class OutlineAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'outline_agent'

    def ready(self):
        self.outline_writer = OutlineWriter()
