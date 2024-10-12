from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
import json

# Create your tests here.

class SupabaseSearchAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('supabase-search')  # Assuming you've named your URL pattern 'supabase-search'

    @patch('paper_lists_retrive.services.Supabase_service.Supabase.search_documents')
    def test_successful_search(self, mock_search):
        # Mock the search_documents method to return a predefined result
        mock_search.return_value = [{"id": 1, "title": "Test Document"}]

        response = self.client.get(self.url, {'query': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"id": 1, "title": "Test Document"}])
        mock_search.assert_called_once_with('test', 100, 0.7, None)

    def test_missing_query_parameter(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Query parameter is required"})

    def test_invalid_match_count(self):
        response = self.client.get(self.url, {'query': 'test', 'match_count': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_match_threshold(self):
        response = self.client.get(self.url, {'query': 'test', 'match_threshold': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_filters_json(self):
        response = self.client.get(self.url, {'query': 'test', 'filters': 'invalid json'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Invalid JSON format for filters"})

    @patch('paper_lists_retrive.services.Supabase_service.Supabase.search_documents')
    def test_search_with_all_parameters(self, mock_search):
        mock_search.return_value = [{"id": 1, "title": "Test Document"}]

        filters = json.dumps({"year": 2023})
        response = self.client.get(self.url, {
            'query': 'test',
            'match_count': 50,
            'match_threshold': 0.8,
            'filters': filters
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_search.assert_called_once_with('test', 50, 0.8, {"year": 2023})

    @patch('paper_lists_retrive.services.Supabase_service.Supabase.search_documents')
    def test_search_documents_error(self, mock_search):
        # Simulate an error in the search_documents method
        mock_search.side_effect = Exception("Search error")

        response = self.client.get(self.url, {'query': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
