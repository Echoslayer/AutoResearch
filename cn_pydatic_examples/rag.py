"""使用 PydanticAI 的檢索增強生成 (RAG) 範例，結合向量檢索來增強聊天代理功能。

運行 pgvector 的指令：

    mkdir postgres-data
    docker run --rm -e POSTGRES_PASSWORD=postgres \
        -p 54320:5432 \
        -v `pwd`/postgres-data:/var/lib/postgresql/data \
        pgvector/pgvector:pg17

構建搜索資料庫的指令：

    uv run -m pydantic_ai_examples.rag build

向代理詢問問題的指令：

    uv run -m pydantic_ai_examples.rag search "How do I configure logfire to work with FastAPI?"
"""

from __future__ import annotations as _annotations

import asyncio
import re
import sys
import unicodedata
from contextlib import asynccontextmanager
from dataclasses import dataclass

import asyncpg
import httpx
import logfire
import pydantic_core
from openai import AsyncOpenAI
from pydantic import TypeAdapter
from typing_extensions import AsyncGenerator

from pydantic_ai import RunContext
from pydantic_ai.agent import Agent

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_asyncpg()  # 與 asyncpg 整合，用於數據庫操作日誌

@dataclass
class Deps:
    """依賴類型，包含 OpenAI 和資料庫連接池。"""
    openai: AsyncOpenAI
    pool: asyncpg.Pool


# 初始化代理，使用 OpenAI 的 GPT 模型
agent = Agent('openai:gpt-4o', deps_type=Deps)


@agent.tool
async def retrieve(context: RunContext[Deps], search_query: str) -> str:
    """根據搜索查詢檢索文檔部分。

    參數:
        context: 呼叫上下文。
        search_query: 搜索查詢字符串。
    """
    with logfire.span(
        '創建查詢的嵌入向量 {search_query=}', search_query=search_query
    ):
        embedding = await context.deps.openai.embeddings.create(
            input=search_query,
            model='text-embedding-3-small',
        )

    # 確保嵌入向量生成成功
    assert (
        len(embedding.data) == 1
    ), f'預期 1 個嵌入向量，實際獲得 {len(embedding.data)}, 查詢: {search_query!r}'
    embedding = embedding.data[0].embedding
    embedding_json = pydantic_core.to_json(embedding).decode()

    # 查詢與嵌入向量相似的文檔部分
    rows = await context.deps.pool.fetch(
        'SELECT url, title, content FROM doc_sections ORDER BY embedding <-> $1 LIMIT 8',
        embedding_json,
    )
    return '\n\n'.join(
        f'# {row["title"]}\n文檔 URL: {row["url"]}\n\n{row["content"]}\n'
        for row in rows
    )


async def run_agent(question: str):
    """運行代理，執行基於 RAG 的問題回答。"""
    openai = AsyncOpenAI()
    logfire.instrument_openai(openai)

    logfire.info('詢問 "{question}"', question=question)

    async with database_connect(False) as pool:
        deps = Deps(openai=openai, pool=pool)
        answer = await agent.run(question, deps=deps)
    print(answer.data)


#######################################################
# 以下部分用於構建搜索資料庫，以及一些工具函數。              #
#######################################################

# 文檔的 JSON URL
DOCS_JSON = (
    'https://gist.githubusercontent.com/'
    'samuelcolvin/4b5bb9bb163b1122ff17e29e48c10992/raw/'
    '80c5925c42f1442c24963aaf5eb1a324d47afe95/logfire_docs.json'
)


async def build_search_db():
    """構建搜索資料庫。"""
    async with httpx.AsyncClient() as client:
        response = await client.get(DOCS_JSON)
        response.raise_for_status()
    sections = sessions_ta.validate_json(response.content)

    openai = AsyncOpenAI()
    logfire.instrument_openai(openai)

    async with database_connect(True) as pool:
        with logfire.span('創建資料庫模式'):
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(DB_SCHEMA)

        sem = asyncio.Semaphore(10)
        async with asyncio.TaskGroup() as tg:
            for section in sections:
                tg.create_task(insert_doc_section(sem, openai, pool, section))


async def insert_doc_section(
    sem: asyncio.Semaphore,
    openai: AsyncOpenAI,
    pool: asyncpg.Pool,
    section: DocsSection,
) -> None:
    """插入文檔部分到資料庫。"""
    async with sem:
        url = section.url()
        exists = await pool.fetchval('SELECT 1 FROM doc_sections WHERE url = $1', url)
        if exists:
            logfire.info('跳過 {url=}', url=url)

        with logfire.span('創建嵌入向量 {url=}', url=url):
            embedding = await openai.embeddings.create(
                input=section.embedding_content(),
                model='text-embedding-3-small',
            )
        assert (
            len(embedding.data) == 1
        ), f'預期 1 個嵌入向量，實際獲得 {len(embedding.data)}, 文檔部分: {section}'
        embedding = embedding.data[0].embedding
        embedding_json = pydantic_core.to_json(embedding).decode()
        await pool.execute(
            'INSERT INTO doc_sections (url, title, content, embedding) VALUES ($1, $2, $3, $4)',
            url,
            section.title,
            section.content,
            embedding_json,
        )


@dataclass
class DocsSection:
    """文檔部分結構。"""
    id: int
    parent: int | None
    path: str
    level: int
    title: str
    content: str

    def url(self) -> str:
        """生成文檔的 URL。"""
        url_path = re.sub(r'\.md$', '', self.path)
        return (
            f'https://logfire.pydantic.dev/docs/{url_path}/#{slugify(self.title, "-")}'
        )

    def embedding_content(self) -> str:
        """生成嵌入向量所需的內容。"""
        return '\n\n'.join((f'路徑: {self.path}', f'標題: {self.title}', self.content))


sessions_ta = TypeAdapter(list[DocsSection])


@asynccontextmanager
async def database_connect(
    create_db: bool = False,
) -> AsyncGenerator[asyncpg.Pool, None]:
    """管理資料庫連接的上下文管理器。"""
    server_dsn, database = (
        'postgresql://postgres:postgres@localhost:54320',
        'pydantic_ai_rag',
    )
    if create_db:
        with logfire.span('檢查並創建資料庫'):
            conn = await asyncpg.connect(server_dsn)
            try:
                db_exists = await conn.fetchval(
                    'SELECT 1 FROM pg_database WHERE datname = $1', database
                )
                if not db_exists:
                    await conn.execute(f'CREATE DATABASE {database}')
            finally:
                await conn.close()

    pool = await asyncpg.create_pool(f'{server_dsn}/{database}')
    try:
        yield pool
    finally:
        await pool.close()


DB_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS doc_sections (
    id serial PRIMARY KEY,
    url text NOT NULL UNIQUE,
    title text NOT NULL,
    content text NOT NULL,
    -- text-embedding-3-small 返回 1536 維的向量
    embedding vector(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_sections_embedding ON doc_sections USING hnsw (embedding vector_l2_ops);
"""


def slugify(value: str, separator: str, unicode: bool = False) -> str:
    """將字符串轉換為 URL 友好的 slug。"""
    if not unicode:
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(rf'[{separator}\s]+', separator, value)


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else None
    if action == 'build':
        asyncio.run(build_search_db())
    elif action == 'search':
        if len(sys.argv) == 3:
            q = sys.argv[2]
        else:
            q = 'How do I configure logfire to work with FastAPI?'
        asyncio.run(run_agent(q))
    else:
        print(
            'uv run --extra examples -m pydantic_ai_examples.rag build|search',
            file=sys.stderr,
        )
        sys.exit(1)
