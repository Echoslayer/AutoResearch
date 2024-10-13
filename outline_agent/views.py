from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .services.outline_agent_service import OutlineWriter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['topic'],
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING, description='The topic for the outline'),
            'section_num': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of sections', default=8),
            'rag_num': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of RAG papers', default=10),
            'match_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of matching papers', default=1500),
            'max_paper_chunks': openapi.Schema(type=openapi.TYPE_INTEGER, description='Maximum number of paper chunks', default=None),
        },
    ),
    responses={
        200: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'outline': openapi.Schema(type=openapi.TYPE_STRING, description='Generated outline'),
                },
            ),
        ),
        400: 'Bad Request',
        500: 'Internal Server Error',
    },
    operation_description="Generate an outline based on the given topic and parameters",
)
@csrf_exempt
@api_view(['POST'])
def generate_outline(request):
    try:
        data = request.data
        topic = data.get('topic')
        section_num = data.get('section_num', 8)
        rag_num = data.get('rag_num', 10)
        match_count = data.get('match_count', 1500)
        max_paper_chunks = data.get('max_paper_chunks', None)

        if not topic:
            return Response({'error': 'Topic is required'}, status=400)

        outline_writer = OutlineWriter()
        outline = outline_writer.run(topic, section_num, rag_num, match_count, max_paper_chunks)

        return Response({'outline': outline})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

