# LLM Endpoint 模組說明文件

## 模組目的
LLM Endpoint 提供統一的大型語言模型介面，支援多種 LLM 服務的整合。

## 主要功能
- 支援 OpenAI API
- 支援 Ollama 本地部署
- 提供統一的模型調用介面
- 批次處理支援

## 核心元件
- ChatModel 基礎類
- OllamaChat 實現
- OpenAIChat 實現
- 批次生成 API

## 技術特點
- 模型無關的抽象介面
- 彈性的配置選項
- 錯誤處理機制
- 非同步處理支援
