from django.db import models
from django.utils import timezone

class GeneratedOutline(models.Model):
    topic = models.CharField(max_length=255, verbose_name="Topic")
    outline_content = models.TextField(verbose_name="Outline Content")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Creation Time")
    section_count = models.IntegerField(verbose_name="Number of Sections")
    rag_count = models.IntegerField(verbose_name="Number of RAG Papers")
    match_count = models.IntegerField(verbose_name="Number of Matched Papers")
    model_used = models.CharField(max_length=50, default="ollama-8b", verbose_name="Model Used")
    result_folder = models.CharField(max_length=255, blank=True, null=True, verbose_name="Result Folder")

    def __str__(self):
        return f"Outline: {self.topic} (Created at: {self.created_at})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Generated Outline"
        verbose_name_plural = "Generated Outlines"

class OutlineGenerationLog(models.Model):
    outline = models.ForeignKey(GeneratedOutline, on_delete=models.CASCADE, related_name='logs', verbose_name="Related Outline")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    step = models.CharField(max_length=50, verbose_name="Step")
    message = models.TextField(verbose_name="Log Message")

    def __str__(self):
        return f"{self.outline.topic} - {self.step} - {self.timestamp}"

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Outline Generation Log"
        verbose_name_plural = "Outline Generation Logs"
