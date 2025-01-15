# Project Agent Markdown 製作
> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.

## High-Level Objective

- 說明本 Project 中個模組的架構說明文件

## Mid-Level Objective

- 依照個別 Agent 資料夾裡頭的文件，搭配系統文件，產生出說明文件

## Implementation Notes
- 以繁體中文為主
- 以名稱為主
- 每個檔案需說明其主要功能
- 系統文件為 doc/docs/project_entry.md 與 README.md

## Context

### Beginning context
- autoresearch_backend/
- content_agent/
- llm_endpoint/
- outline_agent/
- paper_lists_retrive/
- prompt_generator/
- doc/specs/spec_agent_md_maker.md
- doc/docs/project_entry.md
- README.md

### Ending context  
- autoresearch_backend/
- content_agent/
- llm_endpoint/
- outline_agent/
- paper_lists_retrive/
- prompt_generator/
- doc/specs/spec_agent_md_maker.md
- doc/docs/project_entry.md
- README.md
- doc/docs/doc_autoresearch_backend.md (new)
- doc/docs/doc_content_agent.md (new)
- doc/docs/doc_llm_endpoint.md (new)
- doc/docs/doc_outline_agent.md (new)
- doc/docs/doc_paper_lists_retrive.md (new)
- doc/docs/doc_prompt_generator.md (new)

## Low-Level Tasks
> Ordered from start to finish

1. 檔案說明
```aider
參考 整體文件 doc/docs/project_entry.md 與 README.md
說明，與 <FILE> 檔案 說明 <FILE> 的目的，並將其寫入對應說明文件
```
2. 說明專案的目的
```aider
根據個別檔案說明與整體文件 doc/docs/project_entry.md 與 README.md 
總體說明 agent 資料夾，並將其添加到對應說明文件
```
