"""示例展示如何使用 PydanticAI 根據用戶輸入生成 SQL 查詢。

啟動 Postgres 的指令：

    mkdir postgres-data
    docker run --rm -e POSTGRES_PASSWORD=postgres -p 54320:5432 postgres

運行指令：

    uv run -m pydantic_ai_examples.sql_gen "show me logs from yesterday, with level 'error'"
"""

import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, Union

import asyncpg
import logfire
from annotated_types import MinLen
from devtools import debug
from pydantic import BaseModel, Field
from typing_extensions import TypeAlias

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.format_as_xml import format_as_xml

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_asyncpg()  # 與 asyncpg 整合，用於數據庫操作日誌

# 定義數據庫表的結構
DB_SCHEMA = """
CREATE TABLE records (
    created_at timestamptz,
    start_timestamp timestamptz,
    end_timestamp timestamptz,
    trace_id text,
    span_id text,
    parent_span_id text,
    level log_level,
    span_name text,
    message text,
    attributes_json_schema text,
    attributes jsonb,
    tags text[],
    is_exception boolean,
    otel_status_message text,
    service_name text
);
"""

# 定義一些 SQL 查詢的示例
SQL_EXAMPLES = [
    {
        'request': 'show me records where foobar is false',
        'response': "SELECT * FROM records WHERE attributes->>'foobar' = false",
    },
    {
        'request': 'show me records where attributes include the key "foobar"',
        'response': "SELECT * FROM records WHERE attributes ? 'foobar'",
    },
    {
        'request': 'show me records from yesterday',
        'response': "SELECT * FROM records WHERE start_timestamp::date > CURRENT_TIMESTAMP - INTERVAL '1 day'",
    },
    {
        'request': 'show me error records with the tag "foobar"',
        'response': "SELECT * FROM records WHERE level = 'error' and 'foobar' = ANY(tags)",
    },
]

# 定義依賴類
@dataclass
class Deps:
    conn: asyncpg.Connection  # 數據庫連接對象


# 定義成功生成 SQL 查詢時的返回類型
class Success(BaseModel):
    """成功生成 SQL 查詢時的響應類型。"""
    sql_query: Annotated[str, MinLen(1)]  # SQL 查詢字符串
    explanation: str = Field(
        '', description='對 SQL 查詢的解釋，格式為 markdown'
    )


# 定義無效請求時的返回類型
class InvalidRequest(BaseModel):
    """當用戶輸入不足以生成 SQL 時的響應類型。"""
    error_message: str  # 錯誤消息


Response: TypeAlias = Union[Success, InvalidRequest]  # 響應類型的別名
agent: Agent[Deps, Response] = Agent(
    'gemini-1.5-flash',  # 使用的模型
    result_type=Response,  # 返回的結果類型
    deps_type=Deps,  # 依賴類型
)


# 定義系統提示，向模型提供上下文信息
@agent.system_prompt
async def system_prompt() -> str:
    return f"""\
給定以下 PostgreSQL 記錄表，您的任務是根據用戶的請求生成對應的 SQL 查詢。

數據庫結構:

{DB_SCHEMA}

今天的日期 = {date.today()}

{format_as_xml(SQL_EXAMPLES)}
"""


# 定義結果驗證器，確保生成的 SQL 查詢有效
@agent.result_validator
async def validate_result(ctx: RunContext[Deps], result: Response) -> Response:
    if isinstance(result, InvalidRequest):
        return result

    # 修復模型可能多餘的反斜杠
    result.sql_query = result.sql_query.replace('\\', '')
    if not result.sql_query.upper().startswith('SELECT'):
        raise ModelRetry('請生成 SELECT 查詢')

    # 驗證 SQL 查詢是否能夠在數據庫中執行
    try:
        await ctx.deps.conn.execute(f'EXPLAIN {result.sql_query}')
    except asyncpg.exceptions.PostgresError as e:
        raise ModelRetry(f'無效的查詢: {e}') from e
    else:
        return result


# 主函數，處理用戶的輸入並運行代理
async def main():
    if len(sys.argv) == 1:
        prompt = 'show me logs from yesterday, with level "error"'
    else:
        prompt = sys.argv[1]

    async with database_connect(
        'postgresql://postgres:postgres@localhost:54320', 'pydantic_ai_sql_gen'
    ) as conn:
        deps = Deps(conn)
        result = await agent.run(prompt, deps=deps)
    debug(result.data)


# 數據庫連接的上下文管理器，負責檢查和創建數據庫
@asynccontextmanager
async def database_connect(server_dsn: str, database: str) -> AsyncGenerator[Any, None]:
    with logfire.span('檢查並創建數據庫'):
        conn = await asyncpg.connect(server_dsn)
        try:
            db_exists = await conn.fetchval(
                'SELECT 1 FROM pg_database WHERE datname = $1', database
            )
            if not db_exists:
                await conn.execute(f'CREATE DATABASE {database}')
        finally:
            await conn.close()

    conn = await asyncpg.connect(f'{server_dsn}/{database}')
    try:
        with logfire.span('創建數據庫結構'):
            async with conn.transaction():
                if not db_exists:
                    await conn.execute(
                        "CREATE TYPE log_level AS ENUM ('debug', 'info', 'warning', 'error', 'critical')"
                    )
                await conn.execute(DB_SCHEMA)
        yield conn
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
