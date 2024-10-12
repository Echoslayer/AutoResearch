import os
import numpy as np
import tiktoken
from tqdm import trange, tqdm
import time
import torch
import logging
from prompt_generator.CONSTANT.PROMPTS import (
    ROUGH_OUTLINE_PROMPT,
    MERGING_OUTLINE_PROMPT,
    SUBSECTION_OUTLINE_PROMPT,
    EDIT_FINAL_OUTLINE_PROMPT,
    CHECK_SUBSECTION_OUTLINE_PROMPT,
    SUBSECTION_WRITING_PROMPT,
    CHECK_CITATION_PROMPT
)

logger = logging.getLogger(__name__)

class PromptGenerator:
    @staticmethod
    def generate_prompt(template, params):
        logger.debug(f"Generating prompt with template: {template[:50]}... and params: {params}")
        prompt = template
        if isinstance(prompt, str):
            for k, v in params.items():
                prompt = prompt.replace(f'[{k}]', str(v))
        else:
            logger.error("Template is not a string")
            raise TypeError("Template must be a string")
        logger.debug(f"Generated prompt: {prompt[:50]}...")
        return prompt

    @staticmethod
    def generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num):
        logger.debug(f"Generating rough outline prompt for topic: {topic}, section_num: {section_num}")
        
        if len(papers_chunk) != len(titles_chunk):
            raise ValueError("The number of papers and titles must be the same")
        
        paper_texts = ''.join([f'---\npaper_title: {t}\n\npaper_content:\n\n{p}\n' for t, p in zip(titles_chunk, papers_chunk)])
        paper_texts += '---\n'
        params = {
            'PAPER LIST': paper_texts,
            'TOPIC': topic,
            'SECTION NUM': str(section_num)
        }
        return PromptGenerator.generate_prompt(ROUGH_OUTLINE_PROMPT, params)

    @staticmethod
    def generate_merge_outlines_prompt(topic, outlines, section_num):
        logger.debug(f"Generating merge outlines prompt for topic: {topic}, section_num: {section_num}")
        outline_texts = '' 
        for i, o in enumerate(outlines):
            outline_texts += f'---\noutline_id: {i}\n\noutline_content:\n\n{o}\n'
        outline_texts += '---\n'
        params = {
            'OUTLINE LIST': outline_texts,
            'TOPIC': topic,
            'TOTAL NUMBER OF SECTIONS': str(section_num)
        }
        return PromptGenerator.generate_prompt(MERGING_OUTLINE_PROMPT, params)

    @staticmethod
    def generate_subsection_outline_prompt(topic, section_outline, section_name, section_description, paper_list):
        logger.debug(f"Generating subsection outline prompt for topic: {topic}, section_name: {section_name}")
        paper_texts = ''.join([f'---\npaper_title: {paper["title"]}\n\npaper_content:\n\n{paper["abstract"]}\n' for paper in paper_list])
        paper_texts += '---\n'
        params = {
            'OVERALL OUTLINE': section_outline,
            'SECTION NAME': section_name,
            'SECTION DESCRIPTION': section_description,
            'TOPIC': topic,
            'PAPER LIST': paper_texts
        }
        return PromptGenerator.generate_prompt(SUBSECTION_OUTLINE_PROMPT, params)

    @staticmethod
    def generate_edit_final_outline_prompt(outline, section_num):
        logger.debug(f"Generating edit final outline prompt for section_num: {section_num}")
        params = {
            'OVERALL OUTLINE': outline,
            'TOTAL NUMBER OF SECTIONS': str(section_num)
        }
        return PromptGenerator.generate_prompt(EDIT_FINAL_OUTLINE_PROMPT, params)
    
    @staticmethod
    def generate_check_subsection_outline_prompt(section_name, section_description, current_subsection_outline):
        logger.debug(f"Generating check subsection outline prompt for section_name: {section_name}")
        params = {
            'CURRENT SUBSECTION OUTLINE': current_subsection_outline
        }
        return PromptGenerator.generate_prompt(CHECK_SUBSECTION_OUTLINE_PROMPT, params)

    @staticmethod
    def generate_subsection_writing_prompt(outline, subsection, description, topic, paper_texts, section, subsection_len, citation_num):
        logger.debug(f"Generating subsection writing prompt for topic: {topic}, subsection: {subsection}")
        params = {
            'OVERALL OUTLINE': outline,
            'SUBSECTION NAME': subsection,
            'DESCRIPTION': description,
            'TOPIC': topic,
            'PAPER LIST': paper_texts,
            'SECTION NAME': section,
            'WORD NUM': str(subsection_len),
            'CITATION NUM': str(citation_num)
        }
        return PromptGenerator.generate_prompt(SUBSECTION_WRITING_PROMPT, params)

    @staticmethod
    def generate_check_citation_prompt(topic, paper_list, subsection):
        logger.debug(f"Generating check citation prompt for topic: {topic}, subsection: {subsection}")
        params = {
            'TOPIC': topic,
            'PAPER LIST': paper_list,
            'SUBSECTION': subsection
        }
        return PromptGenerator.generate_prompt(CHECK_CITATION_PROMPT, params)
