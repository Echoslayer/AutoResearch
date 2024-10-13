from django.apps import AppConfig
from content_agent.services.content_agent_service import ContentAgent


class ContentAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content_agent'

    def ready(self):
        self.content_agent = ContentAgent()
