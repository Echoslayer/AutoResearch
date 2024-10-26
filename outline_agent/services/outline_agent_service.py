import requests
import json
from django.conf import settings
from prompt_generator.services.prompt_generator_service import PromptGenerator
from paper_lists_retrive.services.Supabase_service import Supabase
import os
import re
import datetime
import shutil
import logging
from ..config import LLM_ENDPOINT, DEFAULT_SECTION_NUM, DEFAULT_RAG_NUM, DEFAULT_MATCH_COUNT
from ..models import GeneratedOutline, OutlineGenerationLog

logger = logging.getLogger(__name__)

class OutlineWriter:
    def __init__(self):
        self.prompt_generator = PromptGenerator()
        self.llm_endpoint = LLM_ENDPOINT
        self.model_name = settings.DEFAULT_LLM_MODEL
        self.temperature = settings.DEFAULT_LLM_TEMPERATURE
        self.max_tokens = settings.DEFAULT_LLM_MAX_TOKENS
        self.num_ctx = settings.DEFAULT_LLM_NUM_CTX

    def run(self, topic, section_num=DEFAULT_SECTION_NUM, rag_num=DEFAULT_RAG_NUM, match_count=DEFAULT_MATCH_COUNT, max_paper_chunks=None):
        try:
            result_folder = self._create_result_folder(topic)
            self._log_to_file(result_folder, f"Result folder created: {result_folder}")

            outline_instance = GeneratedOutline.objects.create(
                topic=topic,
                section_count=section_num,
                rag_count=rag_num,
                match_count=match_count,
                model_used=self.model_name,
                result_folder=result_folder
            )

            # Step 1: Retrieve papers
            self._log_to_file(result_folder, "Step 1: Retrieving papers")
            search_results = self._retrieve_papers(topic, match_count)
            self._save_step_result(result_folder, 1, "paper_retrieval", search_results)
            self._log_to_file(result_folder, f"Retrieved {len(search_results)} papers")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 1", message="Papers retrieved")

            references_papers = [result['abstract'] for result in search_results]
            references_titles = [result['title'] for result in search_results]
            
            # Step 2: Chunk papers and titles
            self._log_to_file(result_folder, "Step 2: Chunking papers and titles")
            papers_chunks, titles_chunks = self._chunk_papers_and_titles(references_papers, references_titles, max_chunks=max_paper_chunks)
            self._save_step_result(result_folder, 2, "chunked_papers", {"papers_chunks": papers_chunks, "titles_chunks": titles_chunks})
            self._log_to_file(result_folder, f"Created {len(papers_chunks)} paper chunks")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 2", message="Papers and titles chunked")

            # Step 3: Generate rough outlines
            self._log_to_file(result_folder, "Step 3: Generating rough outlines")
            rough_outlines = self._generate_rough_outlines(topic, papers_chunks, titles_chunks, section_num, result_folder)
            self._save_step_result(result_folder, 3, "rough_outlines", rough_outlines)
            self._log_to_file(result_folder, f"Generated {len(rough_outlines)} rough outlines")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 3", message="Rough outlines generated")
            
            # Step 4: Merge outlines
            self._log_to_file(result_folder, "Step 4: Merging outlines")
            merged_outline = self._merge_outlines(topic, rough_outlines, section_num, result_folder)
            self._save_step_result(result_folder, 4, "merged_outline", merged_outline)
            self._log_to_file(result_folder, "Outlines merged")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 4", message="Outlines merged")
            
            # Step 5: Generate subsection outlines
            self._log_to_file(result_folder, "Step 5: Generating subsection outlines")
            sub_outlines = self._generate_subsection_outlines(topic, merged_outline, rag_num, result_folder)
            self._save_step_result(result_folder, 5, "subsection_outlines", sub_outlines)
            self._log_to_file(result_folder, f"Generated {len(sub_outlines)} subsection outlines")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 5", message="Subsection outlines generated")
            
            # Step 6: Process outlines
            self._log_to_file(result_folder, "Step 6: Processing outlines")
            processed_outline = self._process_outlines(merged_outline, sub_outlines)
            self._save_step_result(result_folder, 6, "processed_outline", processed_outline)
            self._log_to_file(result_folder, "Outlines processed")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 6", message="Outlines processed")
            
            # Step 7: Edit final outline
            self._log_to_file(result_folder, "Step 7: Editing final outline")
            final_outline = self._edit_final_outline(processed_outline, result_folder)
            self._save_step_result(result_folder, 7, "final_outline", final_outline)
            self._log_to_file(result_folder, "Final outline edited")
            OutlineGenerationLog.objects.create(outline=outline_instance, step="Step 7", message="Final outline edited")

            # Save final outline
            self._save_outline(result_folder, final_outline)
            self._log_to_file(result_folder, "Final outline saved")
            outline_instance.outline_content = final_outline
            outline_instance.save()

            return final_outline, result_folder, outline_instance
        except Exception as e:
            error_message = f"Error occurred during outline generation process: {str(e)}"
            logger.error(error_message)
            self._log_to_file(result_folder, error_message)
            raise

    def _retrieve_papers(self, topic, match_count):
        try:
            search_results = Supabase.search_documents(topic, match_count=match_count)
            if not search_results:
                raise ValueError(f"No papers found related to the topic '{topic}'")
            return search_results
        except Exception as e:
            error_message = f"Error occurred while retrieving papers: {str(e)}"
            logger.error(error_message)
            raise

    def _create_result_folder(self, topic):
        base_folder = os.path.join(settings.BASE_DIR, "outline_results")
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{topic.replace(' ', '_')}_{timestamp}"
        result_folder = os.path.join(base_folder, folder_name)
        os.makedirs(result_folder)
        return result_folder

    def _save_step_result(self, folder, step_number, step_name, data):
        base_step_number = str(step_number).split('_')[0]
        step_folder = os.path.join(folder, f"step_{base_step_number}")
        if not os.path.exists(step_folder):
            os.makedirs(step_folder)
        
        file_name = f"{step_number}_{step_name}.json"
        file_path = os.path.join(step_folder, file_name)
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._log_to_file(folder, f"Step result saved: {file_path}")

    def _chunk_papers_and_titles(self, papers, titles, chunk_size=14000, max_chunks=None):
        chunks = []
        current_chunk_papers = []
        current_chunk_titles = []
        current_size = 0

        for paper, title in zip(papers, titles):
            if current_size + len(paper) > chunk_size or (max_chunks and len(chunks) >= max_chunks - 1):
                chunks.append((current_chunk_papers, current_chunk_titles))
                current_chunk_papers = []
                current_chunk_titles = []
                current_size = 0
            
            current_chunk_papers.append(paper)
            current_chunk_titles.append(title)
            current_size += len(paper)

        if current_chunk_papers:
            chunks.append((current_chunk_papers, current_chunk_titles))

        if not chunks:
            raise ValueError("Unable to create valid paper chunks")

        return list(zip(*chunks))

    def _save_outline(self, folder, outline):
        outline_file = os.path.join(folder, "final_outline.txt")
        with open(outline_file, "w", encoding='utf-8') as f:
            f.write(outline)
        self._log_to_file(folder, f"Outline saved to: {outline_file}")

    def _generate_rough_outlines(self, topic, papers_chunks, titles_chunks, section_num, result_folder):
        outlines = []
        for i, (papers_chunk, titles_chunk) in enumerate(zip(papers_chunks, titles_chunks)):
            self._log_to_file(result_folder, f"Generating rough outline for chunk {i+1}")
            prompt = self.prompt_generator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)
            self._save_step_result(result_folder, f"3_{i+1}", "rough_outline_prompt", prompt)
            
            try:
                outline = self._generate_text(prompt)
                outline = self._remove_asterisks(outline)
                self._save_step_result(result_folder, f"3_{i+1}", "rough_outline_result", outline)
                outlines.append(outline)
            except Exception as e:
                error_message = f"Error generating rough outline for chunk {i+1}: {str(e)}"
                logger.error(error_message)
                self._log_to_file(result_folder, error_message)
                

        if not outlines:
            raise ValueError("Failed to generate any rough outlines")

        self._log_to_file(result_folder, f"Generated {len(outlines)} rough outlines")
        return outlines

    def _merge_outlines(self, topic, outlines, section_num, result_folder):
        prompt = self.prompt_generator.generate_merge_outlines_prompt(topic, outlines, section_num)
        self._save_step_result(result_folder, "4", "merge_outlines_prompt", prompt)
        
        try:
            merged_outline = self._generate_text(prompt)
            merged_outline = self._remove_asterisks(merged_outline)
            self._save_step_result(result_folder, "4", "merge_outlines_result", merged_outline)
            
            self._log_to_file(result_folder, "Outlines merged")
            return merged_outline
        except Exception as e:
            error_message = f"Error merging outlines: {str(e)}"
            logger.error(error_message)
            self._log_to_file(result_folder, error_message)
            raise

    def _generate_subsection_outlines(self, topic, section_outline, rag_num, result_folder):
        survey_title, survey_sections, survey_section_descriptions = self._extract_title_sections_descriptions(section_outline)
        
        sub_outlines = []
        for i, (section_name, section_description) in enumerate(zip(survey_sections, survey_section_descriptions)):
            self._log_to_file(result_folder, f"Generating subsection outline for section {i+1}: {section_name}")
            try:
                paper_list = Supabase.search_documents(section_description, match_count=rag_num, match_threshold=0.5)
                paper_list = [{'title': item['title'], 'abstract': item['abstract'], 'paper_id': item['paper_id']} for item in paper_list]
                self._save_step_result(result_folder, f"5_{i+1:02d}", "subsection_papers", paper_list)
                
                prompt = self.prompt_generator.generate_subsection_outline_prompt(topic, section_outline, section_name, section_description, paper_list)
                self._save_step_result(result_folder, f"5_{i+1:02d}", "subsection_outline_prompt", prompt)
                
                sub_outline = self._generate_text(prompt)
                sub_outline = self._remove_asterisks(sub_outline)
                self._save_step_result(result_folder, f"5_{i+1:02d}", "subsection_outline_result", sub_outline)
                
                sub_outlines.append(sub_outline)
            except Exception as e:
                error_message = f"Error generating subsection outline for section {i+1}: {str(e)}"
                logger.error(error_message)
                self._log_to_file(result_folder, error_message)
                # Continue with the next section instead of breaking the entire process
        
        if not sub_outlines:
            raise ValueError("Failed to generate any subsection outlines")

        self._log_to_file(result_folder, f"Generated {len(sub_outlines)} subsection outlines")
        return sub_outlines

    def _process_outlines(self, section_outline, sub_outlines):
        sections = self._extract_sections(section_outline)
        merged_outline = ""
        for i, section in enumerate(sections):
            merged_outline += f"Section {i+1}: {section}\n"
            if i < len(sub_outlines):
                subsections, subsection_descriptions = self._extract_subsections_subdescriptions(sub_outlines[i])
                for j, (subsection, description) in enumerate(zip(subsections, subsection_descriptions)):
                    merged_outline += f"Subsection {i+1}.{j+1}: {subsection}\n"
                    merged_outline += f"Description {i+1}.{j+1}: {description}\n"
            merged_outline += "\n"
        return merged_outline

    def _edit_final_outline(self, outline, result_folder):
        prompt = self.prompt_generator.generate_edit_final_outline_prompt(outline, section_num=8)
        self._save_step_result(result_folder, "7", "edit_final_outline_prompt", prompt)
        
        try:
            final_outline = self._generate_text(prompt)
            final_outline = self._remove_asterisks(final_outline)
            self._save_step_result(result_folder, "7", "edit_final_outline_result", final_outline)
            
            self._log_to_file(result_folder, "Final outline edited")
            return final_outline.replace('<format>\n','').replace('</format>','')
        except Exception as e:
            error_message = f"Error editing final outline: {str(e)}"
            logger.error(error_message)
            self._log_to_file(result_folder, error_message)
            raise

    def _generate_text(self, prompt):
        try:
            response = requests.post(f"{self.llm_endpoint}/llm/generate/", json={
                "provider": "ollama",
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "num_ctx": self.num_ctx
            }, timeout=30)
            response.raise_for_status()
            return response.json()["generated_text"]
        except requests.RequestException as e:
            error_message = f"Error generating text: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)

    def _extract_title_sections_descriptions(self, outline):
        lines = outline.split('\n')
        title = lines[0].strip()
        sections = []
        descriptions = []
        current_section = None
        current_description = []

        for line in lines[1:]:
            if line.startswith('Section'):
                if current_section:
                    sections.append(current_section)
                    descriptions.append(' '.join(current_description))
                current_section = line.split(':', 1)[1].strip()
                current_description = []
            elif line.strip():
                current_description.append(line.strip())

        if current_section:
            sections.append(current_section)
            descriptions.append(' '.join(current_description))

        return title, sections, descriptions

    def _extract_sections(self, outline):
        return re.findall(r'Section \d+: (.+)', outline)

    def _extract_subsections_subdescriptions(self, sub_outline):
        subsections = re.findall(r'Subsection \d+(?:\.\d+)*: (.+)', sub_outline)
        descriptions = re.findall(r'Description \d+(?:\.\d+)*: (.+)', sub_outline)
        return subsections, descriptions

    def _log_to_file(self, folder, message):
        log_file = os.path.join(folder, "outline_generation.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}\n"
        
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(log_entry)

    def _remove_asterisks(self, text):
        return re.sub(r'\*\*', '', text)

    def clean_up(self, result_folder):
        try:
            if os.path.exists(result_folder):
                shutil.rmtree(result_folder)
                logger.info(f"Cleaned up result folder: {result_folder}")
        except Exception as e:
            logger.error(f"Error cleaning up result folder: {str(e)}")
