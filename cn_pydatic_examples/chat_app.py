"""使用 FastAPI 建構的簡單聊天應用範例。

運行指令：

    uv run -m pydantic_ai_examples.chat_app
"""

from __future__ import annotations as _annotations

import asyncio
import json
import sqlite3
from collections.abc import AsyncIterator
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, TypeVar
import os

import fastapi
import logfire
from fastapi import Depends, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from typing_extensions import LiteralString, ParamSpec, TypedDict

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

# 如果未配置 logfire，則不會發送任何內容，僅作為範例
logfire.configure(send_to_logfire=os.getenv('LOGFIRE_API_KEY', 'if-token-present'))

# 初始化 Pydantic AI 代理
agent = Agent('openai:gpt-4o-mini')
THIS_DIR = Path(__file__).parent  # 當前文件所在目錄


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    """應用程序的生命週期管理。"""
    async with Database.connect() as db:
        yield {'db': db}


# 創建 FastAPI 應用
app = fastapi.FastAPI(lifespan=lifespan)
logfire.instrument_fastapi(app)  # 日誌工具與 FastAPI 整合


@app.get('/')
async def index() -> FileResponse:
    """返回聊天應用的 HTML 文件。"""
    return FileResponse((THIS_DIR / 'chat_app.html'), media_type='text/html')


@app.get('/chat_app.ts')
async def main_ts() -> FileResponse:
    """返回聊天應用的 TypeScript 代碼。"""
    return FileResponse((THIS_DIR / 'chat_app.ts'), media_type='text/plain')


async def get_db(request: Request) -> Database:
    """從請求中獲取資料庫實例。"""
    return request.state.db


@app.get('/chat/')
async def get_chat(database: Database = Depends(get_db)) -> Response:
    """獲取聊天記錄。"""
    msgs = await database.get_messages()
    return Response(
        b'\n'.join(json.dumps(to_chat_message(m)).encode('utf-8') for m in msgs),
        media_type='text/plain',
    )


class ChatMessage(TypedDict):
    """發送到瀏覽器的消息格式。"""
    role: Literal['user', 'model']  # 消息角色：用戶或模型
    timestamp: str  # 消息時間戳
    content: str  # 消息內容


def to_chat_message(m: ModelMessage) -> ChatMessage:
    """將 ModelMessage 轉換為 ChatMessage 格式。"""
    first_part = m.parts[0]
    if isinstance(m, ModelRequest):
        if isinstance(first_part, UserPromptPart):
            return {
                'role': 'user',
                'timestamp': first_part.timestamp.isoformat(),
                'content': first_part.content,
            }
    elif isinstance(m, ModelResponse):
        if isinstance(first_part, TextPart):
            return {
                'role': 'model',
                'timestamp': m.timestamp.isoformat(),
                'content': first_part.content,
            }
    raise UnexpectedModelBehavior(f'聊天應用中遇到未預期的消息類型: {m}')


@app.post('/chat/')
async def post_chat(
    prompt: Annotated[str, fastapi.Form()], database: Database = Depends(get_db)
) -> StreamingResponse:
    """處理用戶發送的聊天消息並返回響應。"""
    async def stream_messages():
        """以流的形式向客戶端發送消息。"""
        # 立即發送用戶的消息
        yield (
            json.dumps(
                {
                    'role': 'user',
                    'timestamp': datetime.now(tz=timezone.utc).isoformat(),
                    'content': prompt,
                }
            ).encode('utf-8')
            + b'\n'
        )
        # 獲取歷史聊天記錄作為上下文
        messages = await database.get_messages()
        # 使用代理運行用戶輸入並生成回覆
        async with agent.run_stream(prompt, message_history=messages) as result:
            async for text in result.stream(debounce_by=0.01):
                # 創建回覆消息並發送
                m = ModelResponse.from_text(content=text, timestamp=result.timestamp())
                yield json.dumps(to_chat_message(m)).encode('utf-8') + b'\n'
        # 將新消息存入資料庫
        await database.add_messages(result.new_messages_json())

    return StreamingResponse(stream_messages(), media_type='text/plain')


P = ParamSpec('P')
R = TypeVar('R')


@dataclass
class Database:
    """用於存儲聊天消息的簡單 SQLite 資料庫。

    SQLite 標準庫是同步的，因此使用線程池執行異步查詢。
    """
    con: sqlite3.Connection  # 資料庫連接
    _loop: asyncio.AbstractEventLoop  # 異步事件循環
    _executor: ThreadPoolExecutor  # 線程池執行器

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, file: Path = THIS_DIR / '.chat_app_messages.sqlite'
    ) -> AsyncIterator[Database]:
        """連接資料庫並返回資料庫實例。"""
        with logfire.span('connect to DB'):
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            con = await loop.run_in_executor(executor, cls._connect, file)
            slf = cls(con, loop, executor)
        try:
            yield slf
        finally:
            await slf._asyncify(con.close)

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        """初始化 SQLite 資料庫連接。"""
        con = sqlite3.connect(str(file))
        con = logfire.instrument_sqlite3(con)
        cur = con.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY, message_list TEXT);'
        )
        con.commit()
        return con

    async def add_messages(self, messages: bytes):
        """將新消息添加到資料庫中。"""
        await self._asyncify(
            self._execute,
            'INSERT INTO messages (message_list) VALUES (?);',
            messages,
            commit=True,
        )
        await self._asyncify(self.con.commit)

    async def get_messages(self) -> list[ModelMessage]:
        """從資料庫中獲取消息記錄。"""
        c = await self._asyncify(
            self._execute, 'SELECT message_list FROM messages ORDER BY id'
        )
        rows = await self._asyncify(c.fetchall)
        messages: list[ModelMessage] = []
        for row in rows:
            messages.extend(ModelMessagesTypeAdapter.validate_json(row[0]))
        return messages

    def _execute(
        self, sql: LiteralString, *args: Any, commit: bool = False
    ) -> sqlite3.Cursor:
        """執行 SQL 語句。"""
        cur = self.con.cursor()
        cur.execute(sql, args)
        if commit:
            self.con.commit()
        return cur

    async def _asyncify(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        """在線程池中執行同步函數並返回結果。"""
        return await self._loop.run_in_executor(
            self._executor,
            partial(func, **kwargs),
            *args,
        )


if __name__ == '__main__':
    import uvicorn

    # 運行應用
    uvicorn.run(
        'pydantic_ai_examples.chat_app:app', reload=True, reload_dirs=[str(THIS_DIR)]
    )
