from django.test import TestCase
from .services.prompt_generator_service import PromptGenerator
from .CONSTANT.PROMPTS import ROUGH_OUTLINE_PROMPT

# Create your tests here.

class PromptGeneratorTests(TestCase):
    def test_generate_rough_outline_prompt(self):
        # Test data
        topic = "The Impact of Artificial Intelligence on Modern Healthcare"
        titles_chunk = [
            "AI in Diagnostics: A Game Changer for Medical Imaging",
            "Machine Learning Algorithms for Predicting Patient Outcomes",
            "Ethical Considerations in AI-Assisted Medical Decision Making"
        ]
        papers_chunk = [
            "This paper discusses how AI is revolutionizing medical imaging...",
            "This study explores various machine learning algorithms for predicting patient outcomes...",
            "This article examines the ethical implications of using AI in medical decision-making..."
        ]
        section_num = 5

        # Generate the prompt
        prompt = PromptGenerator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)

        # Assertions
        self.assertIsInstance(prompt, str)
        self.assertIn(topic, prompt)
        self.assertIn(str(section_num), prompt)
        for title in titles_chunk:
            self.assertIn(title, prompt)
        for paper in papers_chunk:
            self.assertIn(paper, prompt)
        self.assertIn("Title:", prompt)
        self.assertIn("Section 1:", prompt)
        self.assertIn("Description 1:", prompt)

    def test_generate_rough_outline_prompt_with_empty_lists(self):
        # Test with empty lists
        topic = "Empty Topic"
        titles_chunk = []
        papers_chunk = []
        section_num = 3

        prompt = PromptGenerator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)

        self.assertIsInstance(prompt, str)
        self.assertIn(topic, prompt)
        self.assertIn(str(section_num), prompt)

    def test_generate_rough_outline_prompt_with_mismatched_lists(self):
        # Test with mismatched list lengths
        topic = "Mismatched Topic"
        titles_chunk = ["Title 1", "Title 2"]
        papers_chunk = ["Paper 1"]
        section_num = 2

        with self.assertRaises(ValueError):
            PromptGenerator.generate_rough_outline_prompt(topic, papers_chunk, titles_chunk, section_num)
