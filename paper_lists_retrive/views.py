from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.Supabase_service import Supabase
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
from datetime import datetime

class SupabaseSearchAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Search documents in Supabase",
        manual_parameters=[
            openapi.Parameter('query', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('match_count', openapi.IN_QUERY, description="Number of matches to return", type=openapi.TYPE_INTEGER, default=10),
            openapi.Parameter('match_threshold', openapi.IN_QUERY, description="Match threshold", type=openapi.TYPE_NUMBER, default=0.5),
            openapi.Parameter('filter_categories', openapi.IN_QUERY, description="Filter categories", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for filtering", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="End date for filtering", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            openapi.Parameter('author_filter', openapi.IN_QUERY, description="Author filter", type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            openapi.Parameter('title_filter', openapi.IN_QUERY, description="Title filter", type=openapi.TYPE_STRING),
            openapi.Parameter('abstract_filter', openapi.IN_QUERY, description="Abstract filter", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request):
        query = request.query_params.get('query')
        match_count = int(request.query_params.get('match_count', 100))
        match_threshold = float(request.query_params.get('match_threshold', 0.7))
        
        if not query:
            return Response({"error": "Query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        filters = {
            'filter_categories': request.query_params.getlist('filter_categories'),
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
            'author_filter': request.query_params.getlist('author_filter'),
            'title_filter': request.query_params.get('title_filter'),
            'abstract_filter': request.query_params.get('abstract_filter')
        }
        
        # Convert date strings to datetime objects
        if filters['start_date']:
            try:
                filters['start_date'] = datetime.fromisoformat(filters['start_date'])
            except ValueError:
                return Response({"error": "Invalid start_date format"}, status=status.HTTP_400_BAD_REQUEST)
        
        if filters['end_date']:
            try:
                filters['end_date'] = datetime.fromisoformat(filters['end_date'])
            except ValueError:
                return Response({"error": "Invalid end_date format"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove empty filters
        filters = {k: v for k, v in filters.items() if v}
        
        results = Supabase.search_documents(query, match_count, match_threshold, filters)
        return Response(results)
