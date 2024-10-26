from django.test import TestCase
from unittest.mock import patch, MagicMock
from .services.outline_agent_service import OutlineWriter
from .models import GeneratedOutline, OutlineGenerationLog
from django.core.cache import cache
from django.conf import settings
import os
import shutil

class OutlineAgentTestCase(TestCase):
    def setUp(self):
        self.outline_writer = OutlineWriter()
        self.test_topic = "人工智能在醫療領域的應用"
        self.test_folder = os.path.join(settings.BASE_DIR, "test_outline_results")
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)

    def tearDown(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    @patch('outline_agent.services.outline_agent_service.Supabase')
    @patch('outline_agent.services.outline_agent_service.requests.post')
    def test_generate_outline(self, mock_post, mock_supabase):
        # 模擬 Supabase 搜索結果
        mock_supabase.search_documents.return_value = [
            {'title': '測試論文1', 'abstract': '這是測試論文1的摘要。', 'paper_id': '1'},
            {'title': '測試論文2', 'abstract': '這是測試論文2的摘要。', 'paper_id': '2'},
        ]

        # 模擬 LLM 生成的回應
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"generated_text": "這是一個生成的大綱。"}

        # 執行大綱生成
        outline, result_folder, outline_instance = self.outline_writer.run(self.test_topic, section_num=3, rag_num=2, match_count=2)

        # 驗證結果
        self.assertIsNotNone(outline)
        self.assertIn("這是一個生成的大綱", outline)
        self.assertTrue(os.path.exists(result_folder))
        self.assertIsInstance(outline_instance, GeneratedOutline)

        # 驗證是否調用了正確的方法
        mock_supabase.search_documents.assert_called()
        mock_post.assert_called()

    def test_chunk_papers_and_titles(self):
        papers = ["摘要1" * 1000, "摘要2" * 1000, "摘要3" * 1000]
        titles = ["標題1", "標題2", "標題3"]

        papers_chunks, titles_chunks = self.outline_writer._chunk_papers_and_titles(papers, titles)

        self.assertEqual(len(papers_chunks), 3)
        self.assertEqual(len(titles_chunks), 3)

    def test_process_outlines(self):
        section_outline = "Section 1: 主要章節\nSection 2: 次要章節"
        sub_outlines = [
            "Subsection 1: 子章節1\nDescription 1: 描述1",
            "Subsection 2: 子章節2\nDescription 2: 描述2"
        ]

        processed_outline = self.outline_writer._process_outlines(section_outline, sub_outlines)

        self.assertIn("Section 1: 主要章節", processed_outline)
        self.assertIn("Subsection 1: 子章節1", processed_outline)
        self.assertIn("Description 1: 描述1", processed_outline)

    def test_remove_asterisks(self):
        text_with_asterisks = "這是一個**粗體**文本"
        cleaned_text = self.outline_writer._remove_asterisks(text_with_asterisks)
        self.assertEqual(cleaned_text, "這是一個粗體文本")

    def test_create_result_folder(self):
        folder = self.outline_writer._create_result_folder(self.test_topic)
        self.assertIn(self.test_topic.replace(' ', '_'), folder)
        self.assertTrue(os.path.exists(folder))

    @patch('builtins.open', new_callable=MagicMock)
    def test_save_step_result(self, mock_open):
        self.outline_writer._save_step_result(self.test_folder, 1, "test_step", "測試數據")
        mock_open.assert_called()
        mock_open().write.assert_called()

class GeneratedOutlineModelTestCase(TestCase):
    def test_create_generated_outline(self):
        outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )
        self.assertEqual(GeneratedOutline.objects.count(), 1)
        self.assertEqual(outline.topic, "測試主題")
        self.assertEqual(outline.section_count, 5)

    def test_generated_outline_str_method(self):
        outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )
        self.assertIn("測試主題", str(outline))
        self.assertIn("創建於", str(outline))

class OutlineGenerationLogModelTestCase(TestCase):
    def setUp(self):
        self.outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )

    def test_create_outline_generation_log(self):
        log = OutlineGenerationLog.objects.create(
            outline=self.outline,
            step="測試步驟",
            message="這是一條測試日誌消息"
        )
        self.assertEqual(OutlineGenerationLog.objects.count(), 1)
        self.assertEqual(log.step, "測試步驟")
        self.assertEqual(log.message, "這是一條測試日誌消息")

    def test_outline_generation_log_str_method(self):
        log = OutlineGenerationLog.objects.create(
            outline=self.outline,
            step="測試步驟",
            message="這是一條測試日誌消息"
        )
        self.assertIn("測試主題", str(log))
        self.assertIn("測試步驟", str(log))

class OutlineAgentSignalsTestCase(TestCase):from django.test import TestCase
from unittest.mock import patch, MagicMock
from .services.outline_agent_service import OutlineWriter
from .models import GeneratedOutline, OutlineGenerationLog
from django.core.cache import cache
from django.conf import settings
import os
import shutil

class OutlineAgentTestCase(TestCase):
    def setUp(self):
        self.outline_writer = OutlineWriter()
        self.test_topic = "人工智能在醫療領域的應用"
        self.test_folder = os.path.join(settings.BASE_DIR, "test_outline_results")
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)

    def tearDown(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    @patch('outline_agent.services.outline_agent_service.Supabase')
    @patch('outline_agent.services.outline_agent_service.requests.post')
    def test_generate_outline(self, mock_post, mock_supabase):
        mock_supabase.search_documents.return_value = [
            {'title': '測試論文1', 'abstract': '這是測試論文1的摘要。', 'paper_id': '1'},
            {'title': '測試論文2', 'abstract': '這是測試論文2的摘要。', 'paper_id': '2'},
        ]

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"generated_text": "這是一個生成的大綱。"}

        outline, result_folder, outline_instance = self.outline_writer.run(self.test_topic, section_num=3, rag_num=2, match_count=2)

        self.assertIsNotNone(outline)
        self.assertIn("這是一個生成的大綱", outline)
        self.assertTrue(os.path.exists(result_folder))
        self.assertIsInstance(outline_instance, GeneratedOutline)

        mock_supabase.search_documents.assert_called()
        mock_post.assert_called()

    def test_chunk_papers_and_titles(self):
        papers = ["摘要1" * 1000, "摘要2" * 1000, "摘要3" * 1000]
        titles = ["標題1", "標題2", "標題3"]

        papers_chunks, titles_chunks = self.outline_writer._chunk_papers_and_titles(papers, titles)

        self.assertEqual(len(papers_chunks), 3)
        self.assertEqual(len(titles_chunks), 3)

    def test_process_outlines(self):
        section_outline = "Section 1: 主要章節\nSection 2: 次要章節"
        sub_outlines = [
            "Subsection 1: 子章節1\nDescription 1: 描述1",
            "Subsection 2: 子章節2\nDescription 2: 描述2"
        ]

        processed_outline = self.outline_writer._process_outlines(section_outline, sub_outlines)

        self.assertIn("Section 1: 主要章節", processed_outline)
        self.assertIn("Subsection 1: 子章節1", processed_outline)
        self.assertIn("Description 1: 描述1", processed_outline)

    def test_remove_asterisks(self):
        text_with_asterisks = "這是一個**粗體**文本"
        cleaned_text = self.outline_writer._remove_asterisks(text_with_asterisks)
        self.assertEqual(cleaned_text, "這是一個粗體文本")

    def test_create_result_folder(self):
        folder = self.outline_writer._create_result_folder(self.test_topic)
        self.assertIn(self.test_topic.replace(' ', '_'), folder)
        self.assertTrue(os.path.exists(folder))

    @patch('builtins.open', new_callable=MagicMock)
    def test_save_step_result(self, mock_open):
        self.outline_writer._save_step_result(self.test_folder, 1, "test_step", "測試數據")
        mock_open.assert_called()
        mock_open().write.assert_called()

class OutlineAgentModelABTestCase(TestCase):
    def setUp(self):
        self.outline_writer = OutlineWriter()
        self.test_topic = "人工智能在醫療領域的應用"
        self.test_folder = os.path.join(settings.BASE_DIR, "test_outline_results")
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)

    def tearDown(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    @patch('outline_agent.services.outline_agent_service.Supabase')
    @patch('outline_agent.services.outline_agent_service.requests.post')
    def test_generate_outline_model_ab(self, mock_post, mock_supabase):
        search_results = [
            {'title': '論文1', 'abstract': '摘要1', 'paper_id': '1'},
            {'title': '論文2', 'abstract': '摘要2', 'paper_id': '2'},
        ]
        mock_supabase.search_documents.return_value = search_results

        model_responses = {
            "ollama-8b": "這是 ollama-8b 模型生成的大綱。",
            "ollama-70b": "這是 ollama-70b 模型生成的大綱。"
        }

        results = {}

        for model in ["ollama-8b", "ollama-70b"]:
            mock_post.return_value.json.return_value = {"generated_text": model_responses[model]}
            
            outline, result_folder, outline_instance = self.outline_writer.run(
                self.test_topic, 
                section_num=3, 
                rag_num=2, 
                match_count=2,
                model_name=model
            )

            results[model] = {
                "outline": outline,
                "result_folder": result_folder,
                "outline_instance": outline_instance
            }

        self.assertNotEqual(results["ollama-8b"]["outline"], results["ollama-70b"]["outline"], 
                            "ollama-8b 和 ollama-70b 的大綱應該不同")
        self.assertIn("ollama-8b 模型生成的大綱", results["ollama-8b"]["outline"])
        self.assertIn("ollama-70b 模型生成的大綱", results["ollama-70b"]["outline"])

        for model in ["ollama-8b", "ollama-70b"]:
            self.assertTrue(os.path.exists(results[model]["result_folder"]))
            self.assertIsInstance(results[model]["outline_instance"], GeneratedOutline)

class GeneratedOutlineModelTestCase(TestCase):
    def test_create_generated_outline(self):
        outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )
        self.assertEqual(GeneratedOutline.objects.count(), 1)
        self.assertEqual(outline.topic, "測試主題")
        self.assertEqual(outline.section_count, 5)

    def test_generated_outline_str_method(self):
        outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )
        self.assertIn("測試主題", str(outline))
        self.assertIn("創建於", str(outline))

class OutlineGenerationLogModelTestCase(TestCase):
    def setUp(self):
        self.outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )

    def test_create_outline_generation_log(self):
        log = OutlineGenerationLog.objects.create(
            outline=self.outline,
            step="測試步驟",
            message="這是一條測試日誌消息"
        )
        self.assertEqual(OutlineGenerationLog.objects.count(), 1)
        self.assertEqual(log.step, "測試步驟")
        self.assertEqual(log.message, "這是一條測試日誌消息")

    def test_outline_generation_log_str_method(self):
        log = OutlineGenerationLog.objects.create(
            outline=self.outline,
            step="測試步驟",
            message="這是一條測試日誌消息"
        )
        self.assertIn("測試主題", str(log))
        self.assertIn("測試步驟", str(log))

class OutlineAgentSignalsTestCase(TestCase):
    def setUp(self):
        self.outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )

    @patch('outline_agent.signals.cache')
    def test_outline_post_save_signal(self, mock_cache):
        self.outline.topic = "更新的測試主題"
        self.outline.save()

        mock_cache.set.assert_called_with(f"outline_{self.outline.id}", self.outline, timeout=settings.OUTLINE_CACHE_TIMEOUT)

    @patch('outline_agent.signals.os.remove')
    @patch('outline_agent.signals.cache')
    def test_outline_pre_delete_signal(self, mock_cache, mock_os_remove):
        self.outline.result_folder = "/test/folder"
        self.outline.delete()

        mock_os_remove.assert_called_with("/test/folder")
        mock_cache.delete.assert_called_with(f"outline_{self.outline.id}")
    def setUp(self):
        self.outline = GeneratedOutline.objects.create(
            topic="測試主題",
            outline_content="這是測試大綱內容",
            section_count=5,
            rag_count=10,
            match_count=100
        )

    @patch('outline_agent.signals.cache')
    def test_outline_post_save_signal(self, mock_cache):
        self.outline.topic = "更新的測試主題"
        self.outline.save()

        mock_cache.set.assert_called_with(f"outline_{self.outline.id}", self.outline, timeout=settings.OUTLINE_CACHE_TIMEOUT)

    @patch('outline_agent.signals.os.remove')
    @patch('outline_agent.signals.cache')
    def test_outline_pre_delete_signal(self, mock_cache, mock_os_remove):
        self.outline.result_folder = "/test/folder"
        self.outline.delete()

        mock_os_remove.assert_called_with("/test/folder")
        mock_cache.delete.assert_called_with(f"outline_{self.outline.id}")
