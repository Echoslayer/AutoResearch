# AutoResearch Backend 模組說明文件

## 模組目的
AutoResearch Backend 是整個系統的核心配置模組，負責整合所有其他模組並提供基礎設施支援。

## 主要功能
- Django 專案的主要配置
- URL 路由管理
- 全域設定管理
- API 文件整合 (Swagger/OpenAPI)
- 資料庫配置
- 中間件配置

## 關鍵檔案
- settings.py: 系統核心設定
- urls.py: URL 路由配置
- wsgi.py: WSGI 應用配置
- asgi.py: ASGI 應用配置

## 技術特點
- 採用 Django 5.1 框架
- RESTful API 支援
- 完整的 API 文件
- 模組化設計
