import os
from typing import List
import threading
import tiktoken
from tqdm import trange
import time
import requests
import random
import json
import logging
import re

class tokenCounter():

    def __init__(self) -> None:
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.model_price = {}
        
    def num_tokens_from_string(self, string:str) -> int:
        return len(self.encoding.encode(string))

    def num_tokens_from_list_string(self, list_string):
        num = 0
        for i, s in enumerate(list_string):
            try:
                # Convert to string if not already a string
                s = str(s) if not isinstance(s, str) else s
                num += len(self.encoding.encode(s))
            except Exception as e:
                logging.error(f"Error processing item {i} in list_string: {e}")
                logging.error(f"Problematic item: {s}")
                raise  # Re-raise the exception after logging
        return num
    
    def compute_price(self, input_tokens, output_tokens, model):
        return (input_tokens/1000) * self.model_price[model][0] + (output_tokens/1000) * self.model_price[model][1]

    def text_truncation(self,text, max_len = 1000):
        encoded_id = self.encoding.encode(text, disallowed_special=())
        return self.encoding.decode(encoded_id[:min(max_len,len(encoded_id))])
 
def extract_title_sections_descriptions(outline):
    title = outline.split('Title: ')[1].split('\n')[0]
    sections, descriptions = [], []
    for i in range(100):
        if f'Section {i+1}' in outline:
            sections.append(outline.split(f'Section {i+1}: ')[1].split('\n')[0])
            descriptions.append(outline.split(f'Description {i+1}: ')[1].split('\n')[0])
    return title, sections, descriptions


def extract_sections(outline):
    sections = []
    lines = outline.split('\n')
    for line in lines:
        if line.startswith('Section'):
            sections.append(line.split(': ', 1)[-1].strip())
    return sections

def extract_subsections_subdescriptions(outline):
    subsections, subdescriptions = [], []
    lines = outline.split('\n')

    for line in lines:
        if line.startswith('Subsection'):
            subsections.append(line.split(': ', 1)[-1].strip())
        elif line.startswith('Description'):
            subdescriptions.append(line.split(': ', 1)[-1].strip())

    return subsections, subdescriptions

def chunking(papers, titles, chunk_size=14000, encoding=None):
    if encoding is None:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    paper_chunks, title_chunks = [], []
    total_length = sum(len(encoding.encode(paper)) for paper in papers)
    num_of_chunks = max(1, int(total_length / chunk_size))
    avg_len = int(total_length / num_of_chunks) + 1
    
    current_chunk_papers, current_chunk_titles = [], []
    current_length = 0
    
    for paper, title in zip(papers, titles):
        paper_length = len(encoding.encode(paper))
        if current_length + paper_length > avg_len and current_chunk_papers:
            paper_chunks.append(current_chunk_papers)
            title_chunks.append(current_chunk_titles)
            current_chunk_papers, current_chunk_titles = [], []
            current_length = 0
        
        current_chunk_papers.append(paper)
        current_chunk_titles.append(title)
        current_length += paper_length
    
    if current_chunk_papers:
        paper_chunks.append(current_chunk_papers)
        title_chunks.append(current_chunk_titles)
    
    return paper_chunks, title_chunks

def calculate_similarity(str1, str2):
    """
    Calculate the similarity between two strings using Jaccard similarity.
    
    Args:
    str1 (str): The first string to compare.
    str2 (str): The second string to compare.
    
    Returns:
    float: A value between 0 and 1, where 1 means the strings are identical.
    """
    set1 = set(str1.lower())
    set2 = set(str2.lower())
    
    intersection = set1 & set2
    union = set1 | set2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def extract_citations(markdown_text):
    return list(set(citation.strip() for match in re.findall(r'\[(.*?)\]', markdown_text) for citation in match.split(';')))

def replace_citations_with_numbers(citations, markdown_text):
    # This function is a placeholder. The actual implementation would need to be adapted
    # as it depends on external data and functions not available in this context.
    # Here's a simplified version:
    citation_to_number = {citation: str(i+1) for i, citation in enumerate(citations)}
    
    def replace_match(match):
        citations_in_match = match.group(1).split(';')
        replaced_citations = [citation_to_number.get(citation.strip(), citation) for citation in citations_in_match]
        return '[' + '; '.join(replaced_citations) + ']'

    updated_text = re.sub(r'\[(.*?)\]', replace_match, markdown_text)
    
    references_section = "\n\n## References\n\n"
    for i, citation in enumerate(citations):
        references_section += f"[{i+1}] {citation}\n\n"

    return updated_text + references_section, {v: k for k, v in citation_to_number.items()}

def generate_text(llm_endpoint, prompt, temperature):
    """
    Generate text using the specified LLM endpoint.

    Args:
    llm_endpoint (str): The endpoint URL for the LLM service.
    prompt (str): The prompt to send to the LLM.
    temperature (float): The temperature setting for text generation.

    Returns:
    str: The generated text.

    Raises:
    Exception: If there's an error in text generation.
    """
    response = requests.post(f"{llm_endpoint}/llm/generate/", json={
        "provider": "ollama",
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": 1024,
        "num_ctx": 128000
    })
    if response.status_code == 200:
        return response.json()["generated_text"]
    else:
        error_message = f"Error generating text: {response.text}"
        raise Exception(error_message)


def remove_asterisks(self, text):
    """
        Remove double asterisks from the given text.
        
        Args:
            text (str): The input text containing double asterisks.
        
        Returns:
            str: The text with double asterisks removed.
    """
    return re.sub(r'\*\*', '', text)