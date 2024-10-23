import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .services.outline_agent_service import OutlineWriter
from .models import GeneratedOutline, OutlineGenerationLog
from .config import DEFAULT_SECTION_NUM, DEFAULT_RAG_NUM, DEFAULT_MATCH_COUNT

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['topic'],
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING, description='Topic of the outline'),
            'section_num': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of sections', default=DEFAULT_SECTION_NUM),
            'rag_num': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of RAG papers', default=DEFAULT_RAG_NUM),
            'match_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of matching papers', default=DEFAULT_MATCH_COUNT),
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
                    'outline_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the generated outline'),
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
        section_num = int(data.get('section_num', DEFAULT_SECTION_NUM))
        rag_num = int(data.get('rag_num', DEFAULT_RAG_NUM))
        match_count = int(data.get('match_count', DEFAULT_MATCH_COUNT))
        max_paper_chunks = data.get('max_paper_chunks')
        
        if max_paper_chunks is not None:
            max_paper_chunks = int(max_paper_chunks)

        if not topic:
            return Response({'error': 'Topic is required'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Generating outline for topic: {topic}")
        outline_writer = OutlineWriter()
        
        with transaction.atomic():
            # Step 1: Retrieve papers
            search_results = outline_writer._retrieve_papers(topic, match_count)
            
            # Step 2: Chunk papers and titles
            papers = [result['abstract'] for result in search_results]
            titles = [result['title'] for result in search_results]
            papers_chunks, titles_chunks = outline_writer._chunk_papers_and_titles(papers, titles, max_chunks=max_paper_chunks)
            
            # Step 3: Generate rough outlines
            rough_outlines = outline_writer._generate_rough_outlines(topic, papers_chunks, titles_chunks, section_num, '')
            
            # Step 4: Merge outlines
            merged_outline = outline_writer._merge_outlines(topic, rough_outlines, section_num, '')
            
            # Step 5: Generate subsection outlines
            sub_outlines = outline_writer._generate_subsection_outlines(topic, merged_outline, rag_num, '')
            
            # Step 6: Process outlines
            processed_outline = outline_writer._process_outlines(merged_outline, sub_outlines)
            
            # Step 7: Edit final outline
            final_outline = outline_writer._edit_final_outline(processed_outline, '')
            
            # Step 8: Save final outline
            result_folder = outline_writer._create_result_folder(topic)
            outline_writer._save_outline(result_folder, final_outline)
            
            generated_outline = GeneratedOutline.objects.create(
                topic=topic,
                outline_content=final_outline,
                section_count=section_num,
                rag_count=rag_num,
                match_count=match_count,
                result_folder=result_folder
            )

            OutlineGenerationLog.objects.create(
                outline=generated_outline,
                step="Generation Complete",
                message=f"Successfully generated outline for topic '{topic}'"
            )

        logger.info(f"Successfully generated outline for topic: {topic}")
        return Response({
            'outline': final_outline,
            'outline_id': generated_outline.id
        }, status=status.HTTP_200_OK)

    except ValueError as ve:
        logger.error(f"Invalid input: {str(ve)}")
        return Response({'error': f'Invalid input: {str(ve)}'}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception(f"Unexpected error occurred while generating outline: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('topic', openapi.IN_QUERY, description="Topic to filter outlines", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'outlines': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'topic': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                'section_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        )
                    ),
                },
            ),
        ),
        400: 'Bad Request',
    },
    operation_description="Retrieve a list of generated outlines, optionally filtered by topic",
)
@api_view(['GET'])
def list_outlines(request):
    topic = request.GET.get('topic')
    
    try:
        outlines = GeneratedOutline.objects.all()
        if topic:
            outlines = outlines.filter(topic__icontains=topic)
        
        outlines_data = [{
            'id': outline.id,
            'topic': outline.topic,
            'created_at': outline.created_at,
            'section_count': outline.section_count,
        } for outline in outlines]
        
        return Response({'outlines': outlines_data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(f"Unexpected error occurred while listing outlines: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_PATH, description="ID of the outline to retrieve", type=openapi.TYPE_INTEGER, required=True),
    ],
    responses={
        200: openapi.Response(
            description="Successful response",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'topic': openapi.Schema(type=openapi.TYPE_STRING),
                    'outline_content': openapi.Schema(type=openapi.TYPE_STRING),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                    'section_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'rag_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'match_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        404: 'Not Found',
    },
    operation_description="Retrieve a specific outline by ID",
)
@api_view(['GET'])
def get_outline(request, id):
    try:
        outline = GeneratedOutline.objects.get(id=id)
        outline_data = {
            'id': outline.id,
            'topic': outline.topic,
            'outline_content': outline.outline_content,
            'created_at': outline.created_at,
            'section_count': outline.section_count,
            'rag_count': outline.rag_count,
            'match_count': outline.match_count,
        }
        return Response(outline_data, status=status.HTTP_200_OK)
    except GeneratedOutline.DoesNotExist:
        return Response({'error': 'Outline not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Unexpected error occurred while retrieving outline: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='delete',
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_PATH, description="ID of the outline to delete", type=openapi.TYPE_INTEGER, required=True),
    ],
    responses={
        204: 'Successfully deleted',
        404: 'Not Found',
    },
    operation_description="Delete a specific outline",
)
@api_view(['DELETE'])
def delete_outline(request, id):
    try:
        outline = GeneratedOutline.objects.get(id=id)
        outline.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except GeneratedOutline.DoesNotExist:
        return Response({'error': 'Outline not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Unexpected error occurred while deleting outline: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='put',
    manual_parameters=[
        openapi.Parameter('id', openapi.IN_PATH, description="ID of the outline to update", type=openapi.TYPE_INTEGER, required=True),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING, description='Updated topic'),
            'outline_content': openapi.Schema(type=openapi.TYPE_STRING, description='Updated outline content'),
        },
    ),
    responses={
        200: openapi.Response(
            description="Successfully updated",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'topic': openapi.Schema(type=openapi.TYPE_STRING),
                    'outline_content': openapi.Schema(type=openapi.TYPE_STRING),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                    'section_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'rag_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'match_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        400: 'Bad Request',
        404: 'Not Found',
    },
    operation_description="Update a specific outline",
)
@api_view(['PUT'])
def update_outline(request, id):
    try:
        outline = GeneratedOutline.objects.get(id=id)
        data = request.data
        
        if 'topic' in data:
            outline.topic = data['topic']
        if 'outline_content' in data:
            outline.outline_content = data['outline_content']
        
        outline.save()
        
        OutlineGenerationLog.objects.create(
            outline=outline,
            step="Update",
            message=f"Updated outline '{outline.topic}'"
        )
        
        updated_data = {
            'id': outline.id,
            'topic': outline.topic,
            'outline_content': outline.outline_content,
            'created_at': outline.created_at,
            'section_count': outline.section_count,
            'rag_count': outline.rag_count,
            'match_count': outline.match_count,
        }
        return Response(updated_data, status=status.HTTP_200_OK)
    except GeneratedOutline.DoesNotExist:
        return Response({'error': 'Outline not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Unexpected error occurred while updating outline: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
