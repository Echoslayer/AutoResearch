# AutoResearch 專案說明文件

## 專案目的
AutoResearch 是一個基於 AI 技術的研究論文輔助系統，主要用於協助生成和建構研究論文。系統使用 Django 框架並整合多種 AI 技術，以簡化研究寫作過程。

## 專案架構說明

### 核心模組

1. **llm_endpoint**
   - 負責處理大型語言模型的介面
   - 支援 OpenAI 和 Ollama 等不同的 LLM 服務
   - 提供統一的模型調用介面

2. **outline_agent**
   - 處理論文大綱生成相關功能
   - 負責建構論文結構

3. **content_agent**
   - 處理論文內容生成
   - 管理內容產生流程

4. **prompt_generator**
   - 提供提示詞生成服務
   - 支援多種類型的提示詞模板

5. **paper_lists_retrive**
   - 論文檢索和管理功能
   - 整合 Supabase 資料庫服務

6. **autoresearch_backend**
   - Django 後端主要配置
   - 系統核心設定

### 工具檔案說明

1. **clear_migrate.py**
   - 用於清理資料庫遷移檔案
   - 重置資料庫狀態

2. **clear_pyc.py**
   - 清理 Python 編譯檔案
   - 維護專案整潔度

3. **manage.py**
   - Django 專案管理工具
   - 提供各種管理命令

## 技術堆疊

### 主要框架
- Django 5.1
- Django REST Framework
- drf-yasg (API 文件)

### AI 相關
- OpenAI
- Torch
- Sentence Transformers
- Tiktoken

### 資料庫和存儲
- Supabase
- PostgreSQL

### 部署相關
- Gunicorn
- python-dotenv

## 專案特色
1. 模組化設計，各功能區塊清晰分離
2. 完整的 API 文件支援
3. 彈性的 LLM 模型支援
4. 強大的資料庫整合能力

## 開發指南
專案採用標準的 Django 開發流程，使用 pyproject.toml 進行依賴管理，確保開發環境的一致性。
