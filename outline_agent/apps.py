from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class OutlineAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'outline_agent'
    verbose_name = _("Outline Generator")

    def ready(self):
        try:
            import outline_agent.signals  # noqa F401
        except ImportError:
            logger.warning(_("Unable to import signals module"))

        self.init_app_settings()
        self.check_dependencies()
        self.setup_logging()
        self.initialize_nlp_models()

        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        @receiver(post_migrate)
        def initialize_db(sender, **kwargs):
            if sender.name == self.name:
                self.register_periodic_tasks()

        logger.info(_("Outline Generator application is ready!"))

    def init_app_settings(self):
        if not hasattr(settings, 'OUTLINE_MAX_LENGTH'):
            settings.OUTLINE_MAX_LENGTH = 5000
            logger.info(_("Set default outline max length to 5000"))

        if not hasattr(settings, 'OUTLINE_DEFAULT_SECTIONS'):
            settings.OUTLINE_DEFAULT_SECTIONS = 8
            logger.info(_("Set default outline sections to 8"))

        if not hasattr(settings, 'OUTLINE_CACHE_TIMEOUT'):
            settings.OUTLINE_CACHE_TIMEOUT = 3600  
            logger.info(_("Set outline cache timeout to 1 hour"))

        if not hasattr(settings, 'OUTLINE_GENERATION_TIMEOUT'):
            settings.OUTLINE_GENERATION_TIMEOUT = 300  
            logger.info(_("Set outline generation timeout to 5 minutes"))

    def check_dependencies(self):
        try:
            import requests
            import nltk
            import torch
            nltk.download('punkt', quiet=True)
            logger.info(_("All required dependencies are correctly installed"))
        except ImportError as e:
            logger.error(_("Missing required dependency: {}").format(str(e)))

    def setup_logging(self):
        log_level = getattr(settings, 'OUTLINE_AGENT_LOG_LEVEL', 'INFO')
        logging.getLogger('outline_agent').setLevel(log_level)
        logger.info(_("Log level set to: {}").format(log_level))

    def initialize_nlp_models(self):
        try:
            from transformers import AutoTokenizer, AutoModel
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            self.model = AutoModel.from_pretrained("bert-base-uncased")
            logger.info(_("NLP models initialized successfully"))
        except Exception as e:
            logger.error(_("Failed to initialize NLP models: {}").format(str(e)))

    def register_periodic_tasks(self):
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1,
                period=IntervalSchedule.DAYS,
            )
            PeriodicTask.objects.get_or_create(
                name='Clean expired outlines',
                task='outline_agent.tasks.clean_expired_outlines',
                interval=schedule,
            )
            logger.info(_("Periodic tasks registered successfully"))
        except ImportError:
            logger.warning(_("Unable to import django_celery_beat, periodic tasks not registered"))
        except Exception as e:
            logger.error(_("Failed to register periodic tasks: {}").format(str(e)))
