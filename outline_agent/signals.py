from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from .models import GeneratedOutline, OutlineGenerationLog
import logging
import os
import json

logger = logging.getLogger(__name__)

@receiver(post_save, sender=GeneratedOutline)
def outline_post_save(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New outline created: {instance.topic}")
        create_outline_log(instance, "Creation", f"Outline '{instance.topic}' has been created")
    else:
        logger.info(f"Outline updated: {instance.topic}")
        create_outline_log(instance, "Update", f"Outline '{instance.topic}' has been updated")

    update_outline_cache(instance)
    check_outline_length(instance)
    update_search_index(instance)
    notify_users(instance)

@receiver(pre_delete, sender=GeneratedOutline)
def outline_pre_delete(sender, instance, **kwargs):
    logger.info(f"Outline will be deleted: {instance.topic}")
    delete_outline_files(instance)
    delete_outline_cache(instance)
    remove_from_search_index(instance)
    create_outline_log(instance, "Deletion", f"Outline '{instance.topic}' has been deleted")

def create_outline_log(instance, step, message):
    OutlineGenerationLog.objects.create(
        outline=instance,
        step=step,
        message=message
    )

def update_outline_cache(instance):
    cache_key = f"outline_{instance.id}"
    cache.set(cache_key, instance, timeout=settings.OUTLINE_CACHE_TIMEOUT)

def check_outline_length(instance):
    if len(instance.outline_content) > settings.OUTLINE_MAX_LENGTH:
        logger.warning(f"Outline '{instance.topic}' exceeds maximum length limit")
        create_outline_log(instance, "Warning", f"Outline '{instance.topic}' exceeds maximum length limit")

def delete_outline_files(instance):
    if instance.result_folder:
        try:
            os.remove(instance.result_folder)
            logger.info(f"Deleted outline-related files: {instance.result_folder}")
        except OSError as e:
            logger.error(f"Error deleting outline files: {str(e)}")

def delete_outline_cache(instance):
    cache_key = f"outline_{instance.id}"
    cache.delete(cache_key)

def update_search_index(instance):
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch()
        es.index(index="outlines", id=instance.id, body={
            "topic": instance.topic,
            "content": instance.outline_content,
            "created_at": instance.created_at
        })
        logger.info(f"Outline '{instance.topic}' has been updated in the search index")
    except Exception as e:
        logger.error(f"Error updating search index: {str(e)}")

def remove_from_search_index(instance):
    try:
        from elasticsearch import Elasticsearch
        es = Elasticsearch()
        es.delete(index="outlines", id=instance.id)
        logger.info(f"Outline '{instance.topic}' has been removed from the search index")
    except Exception as e:
        logger.error(f"Error removing from search index: {str(e)}")

def notify_users(instance):
    try:
        from django.core.mail import send_mail
        from django.contrib.auth import get_user_model
        User = get_user_model()
        subscribers = User.objects.filter(outline_subscriptions__outline=instance)
        for user in subscribers:
            send_mail(
                f"Outline Update: {instance.topic}",
                f"The outline '{instance.topic}' you subscribed to has been updated.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        logger.info(f"Notified {subscribers.count()} users about the update of outline '{instance.topic}'")
    except Exception as e:
        logger.error(f"Error notifying users: {str(e)}")
