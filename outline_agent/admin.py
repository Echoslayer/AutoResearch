from django.contrib import admin
from .models import GeneratedOutline
from .services.outline_agent_service import OutlineAgentService

class OutlineWriter:
    def __init__(self):
        self.service = OutlineAgentService()

    def run(self, topic, section_num=8, rag_num=10, match_count=1500, max_paper_chunks=None):
        return self.service.run(topic, section_num, rag_num, match_count, max_paper_chunks)

# Register your models here.
@admin.register(GeneratedOutline)
class GeneratedOutlineAdmin(admin.ModelAdmin):
    list_display = ('topic', 'section_count', 'rag_count', 'match_count', 'model_used', 'created_at')
    search_fields = ('topic',)
    readonly_fields = ('created_at',)  # 移除 'updated_at'

    def generate_outline(self, request, queryset):
        for outline in queryset:
            writer = OutlineWriter()
            writer.run(outline.topic)

    actions = [generate_outline]
