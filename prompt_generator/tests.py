from django.test import TestCase
from .services.prompt_generator_service import PromptGenerator
from .CONSTANT.PROMPTS import ROUGH_OUTLINE_PROMPT

# 創建測試用例
class PromptGeneratorTests(TestCase):
    def test_generate_rough_outline_prompt(self):
        # 測試數據
        topic = "The Impact of Artificial Intelligence on Modern Healthcare"  # 測試主題
        titles_chunk = [
            "AI in Diagnostics: A Game Changer for Medical Imaging",  # 標題1
            "Machine Learning Algorithms for Predicting Patient Outcomes",  # 標題2
            "Ethical Considerations in AI-Assisted Medical Decision Making"  # 標題3
        ]
        papers_chunk = [
            "This paper discusses how AI is revolutionizing medical imaging...",  # 論文摘要1
            "This study explores various machine learning algorithms for predicting patient outcomes...",  # 論文摘要2
            "This article examines the ethical implications of using AI in medical decision-making..."  # 論文摘要3
        ]
        section_num = 5  # 預期生成的段落數

        # 生成提示
        prompt = PromptGenerator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)

        # 斷言測試
        self.assertIsInstance(prompt, str)  # 確保返回結果為字串
        self.assertIn(topic, prompt)  # 確保主題出現在結果中
        self.assertIn(str(section_num), prompt)  # 確保段落數出現在結果中
        for title in titles_chunk:
            self.assertIn(title, prompt)  # 確保每個標題都出現在結果中
        for paper in papers_chunk:
            self.assertIn(paper, prompt)  # 確保每個論文摘要都出現在結果中
        self.assertIn("Title:", prompt)  # 確保包含標題標記
        self.assertIn("Section 1:", prompt)  # 確保包含第一段標記
        self.assertIn("Description 1:", prompt)  # 確保包含第一段描述標記

    def test_generate_rough_outline_prompt_with_empty_lists(self):
        # 測試空清單處理
        topic = "Empty Topic"  # 測試主題
        titles_chunk = []  # 空的標題清單
        papers_chunk = []  # 空的論文清單
        section_num = 3  # 段落數

        prompt = PromptGenerator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)

        self.assertIsInstance(prompt, str)  # 確保返回結果為字串
        self.assertIn(topic, prompt)  # 確保主題出現在結果中
        self.assertIn(str(section_num), prompt)  # 確保段落數出現在結果中

    def test_generate_rough_outline_prompt_with_mismatched_lists(self):
        # 測試清單長度不匹配處理
        topic = "Mismatched Topic"  # 測試主題
        titles_chunk = ["Title 1", "Title 2"]  # 標題清單
        papers_chunk = ["Paper 1"]  # 論文清單
        section_num = 2  # 段落數

        with self.assertRaises(ValueError):
            PromptGenerator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)
