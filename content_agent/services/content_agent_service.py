import os
import re
import requests
import json
from datetime import datetime
from .utils import tokenCounter, calculate_similarity, extract_citations, replace_citations_with_numbers, generate_text, remove_asterisks
from paper_lists_retrive.services.Supabase_service import Supabase
from prompt_generator.services.prompt_generator_service import PromptGenerator
import copy
import shutil
import logging

logger = logging.getLogger(__name__)

class ContentAgent:
    def __init__(self):
        self.prompt_generator = PromptGenerator()
        self.llm_endpoint = "http://0.0.0.0:7777"
        self.result_folder = None

    def run(self, file_path):
        try:
            self._log_to_file("Starting content generation process")
            
            self._log_to_file("Parsing outline file")
            parsed_outline = self.parse_outline(file_path)
            if parsed_outline is None:
                raise ValueError("Failed to parse the outline file")

            self._log_to_file("Extracting topic from outline")
            topic = self._extract_topic_from_outline(parsed_outline)
            if not topic:
                raise ValueError("Unable to extract topic from outline file")

            self.result_folder = self._create_result_folder(topic)
            self._log_to_file(f"Created result folder: {self.result_folder}")

            self._log_to_file(f"Generating content for topic: {topic}")
            raw_survey, raw_survey_with_references, raw_references, refined_survey, refined_survey_with_references, refined_references = self.write(
                topic, parsed_outline, rag_num=10, subsection_len=400, refining=True, reflection=True
            )

            self._log_to_file("Saving generated content")
            self._save_results({
                "raw_survey.txt": raw_survey,
                "raw_survey_with_references.txt": raw_survey_with_references,
                "raw_references.txt": json.dumps(raw_references, indent=2),
                "refined_survey.txt": refined_survey,
                "refined_survey_with_references.txt": refined_survey_with_references,
                "refined_references.txt": json.dumps(refined_references, indent=2)
            })

            self._log_to_file(f"Content generation complete. Results saved in {self.result_folder}")
            return self.result_folder
        except Exception as e:
            self._log_to_file(f"Error generating content: {str(e)}", level="ERROR")
            return None
        
    def _log_to_file(self, message, level="INFO"):
        if self.result_folder is None:
            return  # Skip logging if result_folder is not set yet
        
        log_file = os.path.join(self.result_folder, "content_generation.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}\n"
        
        with open(log_file, "a") as f:
            f.write(log_entry)

    def parse_outline(self, file_path):
        try:
            with open(file_path, 'r') as file:
                outline_content = file.read()
            
            parsed_outline = {'sections': []}
            current_section = None
            current_subsection = None
            
            for line in outline_content.split('\n'):
                line = line.strip()
                if line.startswith('## '):
                    current_section = {
                        'title': line[3:],
                        'description': '',
                        'subsections': []
                    }
                    parsed_outline['sections'].append(current_section)
                    current_subsection = None
                elif line.startswith('### '):
                    if current_section is None:
                        raise ValueError("Subsection found before any section")
                    current_subsection = {
                        'title': line[4:],
                        'description': ''
                    }
                    current_section['subsections'].append(current_subsection)
                elif line.startswith('Description: '):
                    if current_subsection:
                        current_subsection['description'] = line[12:]
                    elif current_section:
                        current_section['description'] = line[12:]
            
            if not parsed_outline['sections']:
                raise ValueError("No sections found in the outline")
            
            return parsed_outline
        except Exception as e:
            logger.error(f"Error parsing outline: {str(e)}")
            return None

    def _extract_topic_from_outline(self, outline):
        if outline and 'sections' in outline and outline['sections']:
            topic = outline['sections'][0]['title']
            return topic
        return None

    def _create_result_folder(self, topic):
        base_folder = "content_results"
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)
        
        folder_name = topic.replace(' ', '_').replace('.', '_')
        result_folder = os.path.join(base_folder, folder_name)
        if os.path.exists(result_folder):
            shutil.rmtree(result_folder)
        os.makedirs(result_folder)
        return result_folder


    def write(self, topic, parsed_outline, rag_num=30, subsection_len=500, refining=True, reflection=True):
        if parsed_outline is None or 'sections' not in parsed_outline:
            self._log_to_file("Invalid or missing parsed outline", level="ERROR")
            raise ValueError("Invalid or missing parsed outline")

        self._log_to_file(f"Starting content generation for topic: {topic}")

        section_content = [[] for _ in range(len(parsed_outline['sections']))]
        section_paper_texts = [[] for _ in range(len(parsed_outline['sections']))]
        
        self._log_to_file("Retrieving papers for subsections")

        self._log_to_file("Preparing paper texts")
        section_paper_texts = self._prepare_paper_texts(parsed_outline, rag_num=30)
        self._save_step_result(3, "section_paper_texts", section_paper_texts)

        self._log_to_file("Writing subsections")
        section_content, subsection_prompts = self._write_subsections(parsed_outline, section_paper_texts, topic, parsed_outline, rag_num, subsection_len)
        self._save_step_result(4, "section_content", {
            "content": section_content,
            "prompts": subsection_prompts
        })

        self._log_to_file("Generating raw survey")
        raw_survey = self._generate_document(parsed_outline, section_content)
        raw_survey_with_references, raw_references = self._process_references(raw_survey)
        self._save_step_result(5, "raw_survey", {
            "raw_survey": raw_survey,
            "raw_survey_with_references": raw_survey_with_references,
            "raw_references": raw_references
        })

        if refining:
            self._log_to_file("Refining subsections")
            final_section_content = self._refine_subsections(topic, parsed_outline, section_content)
            refined_survey = self._generate_document(parsed_outline, final_section_content)
            refined_survey_with_references, refined_references = self._process_references(refined_survey)
            self._save_step_result(6, "refined_survey", {
                "refined_survey": refined_survey,
                "refined_survey_with_references": refined_survey_with_references,
                "refined_references": refined_references
            })
            self._log_to_file("Content generation complete")
            return raw_survey+'\n', raw_survey_with_references+'\n', raw_references, refined_survey+'\n', refined_survey_with_references+'\n', refined_references
        else:
            self._log_to_file("Content generation complete (without refining)")
            return raw_survey+'\n', raw_survey_with_references+'\n', raw_references

    def _save_step_result(self, step_number, step_name, data):
        if self.result_folder is None:
            return  # Skip saving if result_folder is not set yet
        
        # Extract the base step number (e.g., '3' from '3_1' or '3_2')
        base_step_number = str(step_number).split('_')[0]
        step_folder = os.path.join(self.result_folder, f"step_{base_step_number}")
        if not os.path.exists(step_folder):
            os.makedirs(step_folder)
        
        # Use the full step_number in the filename to differentiate sub-steps
        file_name = f"step_{step_number}_{step_name}.txt"
        file_path = os.path.join(step_folder, file_name)
        with open(file_path, "w") as f:
            f.write(str(data))
        self._log_to_file(f"Saved step result: {file_path}")


    def _prepare_paper_texts(self, parsed_outline, rag_num):
        self._log_to_file("Starting paper text preparation")
        section_paper_texts = [[] for _ in range(len(parsed_outline['sections']))]

        total_ids = []
        section_references_ids = [[] for _ in range(len(parsed_outline['sections']))]
        total_references_infos = []
        # Create dictionaries for quick lookup

        
        for i, section in enumerate(parsed_outline['sections']):
            section_references = []
            for (j, sub_description) in enumerate(section['subsections']):
                description = sub_description['description']
                self._log_to_file(f"Processing description: {i}-{j}-{description}")
                references = Supabase.search_documents(description, match_count=rag_num, match_threshold=0.7)
                total_references_infos.extend(references)
                section_references.append([ref['paper_id'] for ref in references])
                total_ids.extend([ref['paper_id'] for ref in references])
            section_references_ids[i] = section_references

        temp_title_dic = {p['paper_id']: p['title'] for p in total_references_infos}
        temp_abs_dic = {p['paper_id']: p['abstract'] for p in total_references_infos}

        for i, section in enumerate(parsed_outline['sections']):
            for references_ids in section_references_ids[i]:
                references_titles = [temp_title_dic[_] for _ in references_ids]
                references_papers = [temp_abs_dic[_] for _ in references_ids]
                paper_texts = ''.join([f'---\n\npaper_title: {t}\n\npaper_content:\n\n{p}\n' for t, p in zip(references_titles, references_papers)])
                paper_texts += '---\n'
                section_paper_texts[i].append(paper_texts)
                self._log_to_file(f"Added paper texts for section {i+1}")

        self._log_to_file("Finished preparing paper texts")
        return section_paper_texts

    def _write_subsections(self, parsed_outline, section_paper_texts, topic, outline, rag_num, subsection_len):
        section_content = [[] for _ in range(len(parsed_outline['sections']))]
        subsection_prompts = [[] for _ in range(len(parsed_outline['sections']))]
        for i, section in enumerate(parsed_outline['sections']):
            contents, prompts = self._write_subsection_with_reflection(i, section_paper_texts[i], topic, outline, section['title'], 
                                            section['subsections'], section['description'], 
                                            rag_num, str(subsection_len))
            section_content[i] = contents
            subsection_prompts[i] = prompts
            self._save_step_result(f"4_{i+1}", f"subsection_{i+1}", {
                "content": contents,
                "prompts": prompts
            })
        return section_content, subsection_prompts

    def _write_subsection_with_reflection(self,index , paper_texts_l, topic, outline, section, subsections, subdescriptions, rag_num=20, subsection_len=1000, citation_num=8):
        writing_prompts = [self.prompt_generator.generate_subsection_writing_prompt(outline, subsection, description, topic, paper_texts, section, subsection_len, citation_num)
                   for subsection, description, paper_texts in zip(subsections, subdescriptions, paper_texts_l)]
        
        contents = []
        for i, prompt in enumerate(writing_prompts):
            self._save_step_result(f"4_{index}_{i+1}", "writing_prompt", prompt)
            response = generate_text(self.llm_endpoint, prompt, temperature=0)
            self._save_step_result(f"4_{index}_{i+1}", "raw_response", response)
            
            try:
                content_data = json.loads(response)
                content = content_data.get('content', '')
                citations = content_data.get('citations', [])
                
                self._log_to_file(f"Generated content with {len(citations)} citations")
                
                contents.append(content)
                self._save_step_result(f"4_{index}_{i+1}", "initial_content", {
                    "content": content,
                    "citations": citations,
                    "subsection_name": content_data['subsection_name']['title'],
                    "section_name": content_data.get('section_name', '')
                })
            except json.JSONDecodeError:
                self._log_to_file(f"Error parsing JSON response for subsection {i+1}", level="ERROR")
                contents.append("")
            except Exception as e:
                self._log_to_file(f"Unexpected error processing subsection {i+1}: {str(e)}", level="ERROR")
                contents.append("")

        reflection_prompts = [self.prompt_generator.generate_check_citation_prompt(topic, paper_texts, content)
                   for content, paper_texts in zip(contents, paper_texts_l)]
        
        reflected_contents = []
        for i, prompt in enumerate(reflection_prompts):
            self._save_step_result(f"4_{index}_{i+1}", f"reflection_prompt", prompt)
            reflected_content = generate_text(self.llm_endpoint, prompt, temperature=0)
            reflected_contents.append(reflected_content)
            self._save_step_result(f"4_{index}_{i+1}", f"reflected_content", reflected_content)
        
        all_prompts = list(zip(writing_prompts, reflection_prompts))
        
        return reflected_contents, all_prompts
        
    def _refine_subsections(self, topic, outline, section_content):
        section_content_even = copy.deepcopy(section_content)
        refinement_prompts = []
        
        for i in range(len(section_content)):
            for j in range(len(section_content[i])):
                if j % 2 == 0:
                    if j == 0:
                        contents = [''] + section_content[i][:2]
                    elif j == (len(section_content[i]) - 1):
                        contents = section_content[i][-2:] + ['']  
                    else:
                        contents = section_content[i][j-1:j+2]
                    refined_content, prompt = self._lce(topic, outline, contents)
                    section_content_even[i][j] = refined_content
                    refinement_prompts.append(prompt)
                    self._save_step_result(f"6_{i+1}_{j+1}", f"refinement_even", {
                        "refined_content": refined_content,
                        "prompt": prompt
                    })

        final_section_content = copy.deepcopy(section_content_even)

        for i in range(len(section_content_even)):
            for j in range(len(section_content_even[i])):
                if j % 2 == 1:
                    if j == (len(section_content_even[i]) - 1):
                        contents = section_content_even[i][-2:] + ['']  
                    else:
                        contents = section_content_even[i][j-1:j+2]
                    refined_content, prompt = self._lce(topic, outline, contents)
                    final_section_content[i][j] = refined_content
                    refinement_prompts.append(prompt)
        
        self._save_step_result(7, "refinement", {
            "refined_content": final_section_content,
            "refinement_prompts": refinement_prompts
        })
        return final_section_content

    def _lce(self, topic, outline, contents):
        if len(contents) >= 3:
            prompt = self.prompt_generator.generate_lce_prompt(topic, contents[0], contents[2], contents[1])
            refined_content = generate_text(self.llm_endpoint, prompt, temperature=0)
            return refined_content, prompt
        else:
            self._log_to_file(f"Not enough elements in contents for LCE. Skipping.", level="WARNING")
            return None, None

    def _generate_document(self, parsed_outline, subsection_contents):
        document = [f"# {parsed_outline['title']}\n\n"]
        
        for i, section in enumerate(parsed_outline['sections']):
            document.append(f"## Section {i+1}: {section['title']}\n")
            if 'description' in section:
                document.append(f"{section['description']}\n\n")
            
            for j, subsection in enumerate(section['subsections']):
                document.append(f"### Subsection {i+1}.{j+1}: {subsection}\n")
                if j < len(section['description']):
                    document.append(f"Description {i+1}.{j+1}: {section['description'][j]}\n\n")
                if i < len(subsection_contents) and j < len(subsection_contents[i]):
                    document.append(subsection_contents[i][j] + "\n\n")
        
        return "\n".join(document)

    def _process_references(self, survey):
        citations = self._extract_citations(survey)
        return self._replace_citations_with_numbers(citations, survey)

    def _extract_citations(self, markdown_text):
        return list(set(citation.strip() for match in re.findall(r'\[(.*?)\]', markdown_text) for citation in match.split(';')))

    def _replace_citations_with_numbers(self, citations, markdown_text):
        all_papers = Supabase.select('arxiv_documents', 'paper_id, title')
        all_titles_to_ids = {p['title']: p['paper_id'] for p in all_papers}
        
        valid_citations = []
        for c in citations:
            best_match = None
            best_similarity = 0
            for db_title in all_titles_to_ids.keys():
                similarity = calculate_similarity(c, db_title)
                if similarity > best_similarity:
                    best_match = db_title
                    best_similarity = similarity
            
            if best_similarity >= 0.9:
                valid_citations.append(best_match)
            else:
                self.logger.warning(f"No similar citation found for '{c}'")
        
        citation_to_ids = {c: all_titles_to_ids[c] for c in valid_citations}
        ids_to_titles = {v: k for k, v in citation_to_ids.items()}
        
        title_to_number = {title: num+1 for num, title in enumerate(valid_citations)}
        number_to_title = {num: title for title, num in title_to_number.items()}
        
        def replace_match(match):
            citations_in_match = match.group(1).split(';')
            replaced_citations = []
            for citation in citations_in_match:
                citation = citation.strip()
                best_match = None
                best_similarity = 0
                for db_citation in citation_to_ids.keys():
                    similarity = calculate_similarity(citation, db_citation)
                    if similarity > best_similarity and similarity >= 0.9:
                        best_match = db_citation
                        best_similarity = similarity
                
                if best_match:
                    paper_id = citation_to_ids[best_match]
                    title = ids_to_titles[paper_id]
                    number = title_to_number[title]
                    replaced_citations.append(str(number))
                else:
                    replaced_citations.append(citation)
            return '[' + '; '.join(replaced_citations) + ']'

        updated_text = re.sub(r'\[(.*?)\]', replace_match, markdown_text)

        references_section = "\n\n## References\n\n"
        references = {num: all_titles_to_ids[title] for num, title in sorted(number_to_title.items())}
        for idx, title in sorted(number_to_title.items()):
            references_section += f"[{idx}] {title.replace('\n','')}\n\n"

        return updated_text + references_section, references
