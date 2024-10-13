from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .services.content_agent_service import ContentAgent
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import traceback
import logging

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='post',
    operation_description="Generate content based on the given outline file",
    manual_parameters=[
        openapi.Parameter(
            name="outline_file",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            required=True,
            description="The outline file"
        ),
    ],
    responses={
        200: openapi.Response(
            description="Content generation successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'result_folder': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        400: 'Bad Request',
        500: 'Internal Server Error',
    },
)
@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def generate_content(request):
    logger.info("Starting content generation process")
    try:
        logger.info("Checking for outline file in request")
        outline_file = request.FILES.get('outline_file')

        if not outline_file:
            logger.error("Missing required outline file")
            return Response({'error': 'Missing required outline file'}, status=400)

        logger.info("Creating upload folder if it doesn't exist")
        upload_folder = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        logger.info("Saving the uploaded file in the upload folder")
        file_name = default_storage.save(os.path.join('uploads', outline_file.name), outline_file)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        content_agent = ContentAgent()
        result_folder = content_agent.run(file_path)

        if result_folder:
            return Response({'result_folder': result_folder}, status=200)
        else:
            return Response({'error': 'Content generation failed'}, status=500)

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error occurred: {str(e)}\n{error_trace}")
        return Response({'error': f'An unexpected error occurred during content generation: {str(e)}'}, status=500)

@api_view(['GET'])
@swagger_auto_schema(
    operation_description="This endpoint is no longer supported",
    responses={
        410: 'Gone',
    },
)
def check_content_status(request):
    return Response({'error': 'This endpoint is no longer supported'}, status=410)
