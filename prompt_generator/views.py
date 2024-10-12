from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.prompt_generator_service import PromptGenerator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

class PromptGeneratorView(APIView):
    @swagger_auto_schema(
        operation_description="Generate a prompt based on the given prompt type and parameters. This endpoint allows for the creation of various types of prompts used in the research process, including rough outlines, merged outlines, subsection outlines, final outline edits, subsection checks, subsection writing, and citation checks.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['prompt_type', 'params'],
            properties={
                'prompt_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Type of prompt to generate",
                    enum=['rough_outline', 'merge_outlines', 'subsection_outline', 'edit_final_outline', 'check_subsection_outline', 'subsection_writing', 'check_citation']
                ),
                'params': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Additional parameters for prompt generation. Required parameters for each prompt_type:\n\n"
                                "- rough_outline: topic, papers_chunk, titles_chunk, section_num\n"
                                "- merge_outlines: topic, outlines, section_num\n"
                                "- subsection_outline: topic, section_outline, section_name, section_description, paper_list\n"
                                "- edit_final_outline: outline, section_num\n"
                                "- check_subsection_outline: section_name, section_description, current_subsection_outline\n"
                                "- subsection_writing: outline, subsection, description, topic, paper_texts, section, subsection_len, citation_num\n"
                                "- check_citation: topic, paper_list, subsection",
                ),
            },
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'prompt': openapi.Schema(type=openapi.TYPE_STRING, description="Generated prompt"),
                },
            )),
            400: openapi.Response('Bad Request', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                },
            )),
            500: openapi.Response('Internal Server Error', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                },
            )),
        },
    )
    def post(self, request):
        """
        Generate a prompt based on the given prompt type and parameters.

        Required parameters for each prompt_type:

        - rough_outline: topic, papers_chunk, titles_chunk, section_num
        - merge_outlines: topic, outlines, section_num
        - subsection_outline: topic, section_outline, section_name, section_description, paper_list
        - edit_final_outline: outline, section_num
        - check_subsection_outline: section_name, section_description, current_subsection_outline
        - subsection_writing: outline, subsection, description, topic, paper_texts, section, subsection_len, citation_num
        - check_citation: topic, paper_list, subsection
        """
        prompt_type = request.data.get('prompt_type')
        params = request.data.get('params', {})

        if not prompt_type:
            return Response({'error': 'prompt_type is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prompt = self.generate_prompt(prompt_type, params)
            return Response({'prompt': prompt}, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(f"ValueError in generate_prompt: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in generate_prompt: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_prompt(self, prompt_type, params):
        prompt_generators = {
            'rough_outline': self.generate_rough_outline_prompt,
            'merge_outlines': self.generate_merge_outlines_prompt,
            'subsection_outline': self.generate_subsection_outline_prompt,
            'edit_final_outline': self.generate_edit_final_outline_prompt,
            'check_subsection_outline': self.generate_check_subsection_outline_prompt,
            'subsection_writing': self.generate_subsection_writing_prompt,
            'check_citation': self.generate_check_citation_prompt
        }

        generator = prompt_generators.get(prompt_type)
        if not generator:
            raise ValueError('Invalid prompt_type')

        try:
            return generator(params)
        except Exception as e:
            logger.error(f"Error in {prompt_type} generator: {str(e)}")
            raise ValueError(f"Error in {prompt_type} generator: {str(e)}")

    def generate_rough_outline_prompt(self, params):
        required_params = ['topic', 'papers_chunk', 'titles_chunk', 'section_num']
        self.check_required_params(params, required_params)
        try:
            section_num = int(params['section_num'])
        except ValueError:
            raise ValueError("'section_num' must be a valid integer")
        
        if not isinstance(params['papers_chunk'], list) or not isinstance(params['titles_chunk'], list):
            raise ValueError("'papers_chunk' and 'titles_chunk' must be lists")
        
        return PromptGenerator.generate_rough_outline_prompt(
            topic=params['topic'],
            papers_chunk=params['papers_chunk'],
            titles_chunk=params['titles_chunk'],
            section_num=section_num
        )

    def generate_merge_outlines_prompt(self, params):
        required_params = ['topic', 'outlines', 'section_num']
        self.check_required_params(params, required_params)
        try:
            return PromptGenerator.generate_merge_outlines_prompt(
                topic=params['topic'],
                outlines=params['outlines'],
                section_num=int(params['section_num'])
            )
        except ValueError as e:
            raise ValueError(f"Invalid value for 'section_num': {str(e)}")

    def generate_subsection_outline_prompt(self, params):
        required_params = ['topic', 'section_outline', 'section_name', 'section_description', 'paper_list']
        self.check_required_params(params, required_params)
        return PromptGenerator.generate_subsection_outline_prompt(**params)

    def generate_edit_final_outline_prompt(self, params):
        required_params = ['outline', 'section_num']
        self.check_required_params(params, required_params)
        try:
            return PromptGenerator.generate_edit_final_outline_prompt(
                outline=params['outline'],
                section_num=int(params['section_num'])
            )
        except ValueError as e:
            raise ValueError(f"Invalid value for 'section_num': {str(e)}")

    def generate_check_subsection_outline_prompt(self, params):
        required_params = ['section_name', 'section_description', 'current_subsection_outline']
        self.check_required_params(params, required_params)
        return PromptGenerator.generate_check_subsection_outline_prompt(**params)

    def generate_subsection_writing_prompt(self, params):
        required_params = ['outline', 'subsection', 'description', 'topic', 'paper_texts', 'section', 'subsection_len', 'citation_num']
        self.check_required_params(params, required_params)
        try:
            return PromptGenerator.generate_subsection_writing_prompt(
                outline=params['outline'],
                subsection=params['subsection'],
                description=params['description'],
                topic=params['topic'],
                paper_texts=params['paper_texts'],
                section=params['section'],
                subsection_len=int(params['subsection_len']),
                citation_num=int(params['citation_num'])
            )
        except ValueError as e:
            raise ValueError(f"Invalid value for 'subsection_len' or 'citation_num': {str(e)}")

    def generate_check_citation_prompt(self, params):
        required_params = ['topic', 'paper_list', 'subsection']
        self.check_required_params(params, required_params)
        return PromptGenerator.generate_check_citation_prompt(**params)

    def check_required_params(self, params, required_params):
        missing_params = [param for param in required_params if param not in params]
        if missing_params:
            raise ValueError(f'Missing required parameters: {", ".join(missing_params)}')

    def handle_string_indices_error(self, params):
        for key, value in params.items():
            if isinstance(value, str):
                try:
                    int(value)
                except ValueError:
                    raise ValueError(f"Parameter '{key}' must be an integer, not a string.")
