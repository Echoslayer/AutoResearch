from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services.outline_agent_service import OutlineWriter
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING, description='The topic to search for'),
            'match_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of papers to retrieve', default=1500),
        },
        required=['topic']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'papers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def retrieve_papers(request):
    """Step 1: Retrieve papers"""
    data = json.loads(request.body)
    topic = data.get('topic')
    match_count = data.get('match_count', 1500)
    
    outline_writer = OutlineWriter()
    search_results = outline_writer._retrieve_papers(topic, match_count)
    
    return JsonResponse({'papers': search_results})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'papers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'titles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'max_paper_chunks': openapi.Schema(type=openapi.TYPE_INTEGER, description='Maximum number of paper chunks'),
        },
        required=['papers', 'titles']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'papers_chunks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'titles_chunks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def chunk_papers(request):
    """Step 2: Chunk papers"""
    data = json.loads(request.body)
    papers = data.get('papers', [])
    titles = data.get('titles', [])
    max_paper_chunks = data.get('max_paper_chunks')
    
    outline_writer = OutlineWriter()
    papers_chunks, titles_chunks = outline_writer._chunk_papers_and_titles(papers, titles, max_chunks=max_paper_chunks)
    
    return JsonResponse({'papers_chunks': papers_chunks, 'titles_chunks': titles_chunks})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING),
            'papers_chunks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'titles_chunks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'section_num': openapi.Schema(type=openapi.TYPE_INTEGER, default=8),
            'result_folder': openapi.Schema(type=openapi.TYPE_STRING, default=''),
        },
        required=['topic', 'papers_chunks', 'titles_chunks']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'rough_outlines': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def generate_rough_outlines(request):
    """Step 3: Generate rough outlines"""
    data = json.loads(request.body)
    topic = data.get('topic')
    papers_chunks = data.get('papers_chunks', [])
    titles_chunks = data.get('titles_chunks', [])
    section_num = data.get('section_num', 8)
    result_folder = data.get('result_folder', '')
    
    outline_writer = OutlineWriter()
    rough_outlines = outline_writer._generate_rough_outlines(topic, papers_chunks, titles_chunks, section_num, result_folder)
    
    return JsonResponse({'rough_outlines': rough_outlines})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING),
            'outlines': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            'section_num': openapi.Schema(type=openapi.TYPE_INTEGER, default=8),
            'result_folder': openapi.Schema(type=openapi.TYPE_STRING, default=''),
        },
        required=['topic', 'outlines']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'merged_outline': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def merge_outlines(request):
    """Step 4: Merge outlines"""
    data = json.loads(request.body)
    topic = data.get('topic')
    outlines = data.get('outlines', [])
    section_num = data.get('section_num', 8)
    result_folder = data.get('result_folder', '')
    
    outline_writer = OutlineWriter()
    merged_outline = outline_writer._merge_outlines(topic, outlines, section_num, result_folder)
    
    return JsonResponse({'merged_outline': merged_outline})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'topic': openapi.Schema(type=openapi.TYPE_STRING),
            'section_outline': openapi.Schema(type=openapi.TYPE_STRING),
            'rag_num': openapi.Schema(type=openapi.TYPE_INTEGER, default=10),
            'result_folder': openapi.Schema(type=openapi.TYPE_STRING, default=''),
        },
        required=['topic', 'section_outline']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'sub_outlines': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def generate_subsection_outlines(request):
    """Step 5: Generate subsection outlines"""
    data = json.loads(request.body)
    topic = data.get('topic')
    section_outline = data.get('section_outline', '')
    rag_num = data.get('rag_num', 10)
    result_folder = data.get('result_folder', '')
    
    outline_writer = OutlineWriter()
    sub_outlines = outline_writer._generate_subsection_outlines(topic, section_outline, rag_num, result_folder)
    
    return JsonResponse({'sub_outlines': sub_outlines})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'section_outline': openapi.Schema(type=openapi.TYPE_STRING),
            'sub_outlines': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
        },
        required=['section_outline', 'sub_outlines']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'processed_outline': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def process_outlines(request):
    """Step 6: Process outlines"""
    data = json.loads(request.body)
    section_outline = data.get('section_outline', '')
    sub_outlines = data.get('sub_outlines', [])
    
    outline_writer = OutlineWriter()
    processed_outline = outline_writer._process_outlines(section_outline, sub_outlines)
    
    return JsonResponse({'processed_outline': processed_outline})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'outline': openapi.Schema(type=openapi.TYPE_STRING),
            'result_folder': openapi.Schema(type=openapi.TYPE_STRING, default=''),
        },
        required=['outline']
    ),
    responses={200: openapi.Response('Successful response', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'final_outline': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))}
)
@csrf_exempt
@require_http_methods(["POST"])
def edit_final_outline(request):
    """Step 7: Edit final outline"""
    data = json.loads(request.body)
    outline = data.get('outline', '')
    result_folder = data.get('result_folder', '')
    
    outline_writer = OutlineWriter()
    final_outline = outline_writer._edit_final_outline(outline, result_folder)
    
    return JsonResponse({'final_outline': final_outline})
