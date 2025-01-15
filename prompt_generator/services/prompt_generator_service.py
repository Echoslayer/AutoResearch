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

# 設置日誌記錄器
logger = logging.getLogger(__name__)

class PromptGenerator:
    @staticmethod
    def generate_prompt(template, params):
        # 根據模板和參數生成提示
        logger.debug(f"正在使用模板生成提示: {template[:50]}... 和參數: {params}")
        prompt = template
        if isinstance(prompt, str):
            # 替換模板中的佔位符為參數值
            for k, v in params.items():
                prompt = prompt.replace(f'[{k}]', str(v))
        else:
            logger.error("模板不是字串類型")
            raise TypeError("模板必須是字串類型")
        logger.debug(f"生成的提示: {prompt[:50]}...")
        return prompt

    @staticmethod
    def generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num):
        # 生成粗略大綱提示
        logger.debug(f"生成粗略大綱提示，主題: {topic}, 段落數: {section_num}")
        
        if len(papers_chunk) != len(titles_chunk):
            # 檢查論文與標題數量是否匹配
            raise ValueError("論文數量和標題數量必須相同")
        
        # 組合論文與標題
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
        # 生成合併大綱提示
        logger.debug(f"生成合併大綱提示，主題: {topic}, 段落數: {section_num}")
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
        # 生成小節大綱提示
        logger.debug(f"生成小節大綱提示，主題: {topic}, 小節名稱: {section_name}")
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
        # 生成編輯最終大綱提示
        logger.debug(f"生成編輯最終大綱提示，段落數: {section_num}")
        params = {
            'OVERALL OUTLINE': outline,
            'TOTAL NUMBER OF SECTIONS': str(section_num)
        }
        return PromptGenerator.generate_prompt(EDIT_FINAL_OUTLINE_PROMPT, params)
    
    @staticmethod
    def generate_check_subsection_outline_prompt(section_name, section_description, current_subsection_outline):
        # 生成檢查小節大綱提示
        logger.debug(f"生成檢查小節大綱提示，小節名稱: {section_name}")
        params = {
            'CURRENT SUBSECTION OUTLINE': current_subsection_outline
        }
        return PromptGenerator.generate_prompt(CHECK_SUBSECTION_OUTLINE_PROMPT, params)

    @staticmethod
    def generate_subsection_writing_prompt(outline, subsection, description, topic, paper_texts, section, subsection_len, citation_num):
        # 生成小節撰寫提示
        logger.debug(f"生成小節撰寫提示，主題: {topic}, 小節: {subsection}")
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
        # 生成檢查引用提示
        logger.debug(f"生成檢查引用提示，主題: {topic}, 小節: {subsection}")
        params = {
            'TOPIC': topic,
            'PAPER LIST': paper_list,
            'SUBSECTION': subsection
        }
        return PromptGenerator.generate_prompt(CHECK_CITATION_PROMPT, params)
