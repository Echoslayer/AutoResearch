"""此範例展示如何使用 `rich` 庫從代理流式輸出 Markdown，並顯示在終端。

運行指令：

    uv run -m pydantic_ai_examples.stream_markdown
"""

import asyncio
import os

import logfire
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.markdown import CodeBlock, Markdown
from rich.syntax import Syntax
from rich.text import Text

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire=os.getenv('LOGFIRE_API_KEY', ''))

# 初始化代理
agent = Agent()

# 定義模型列表以及所需的環境變數
models: list[tuple[KnownModelName, str]] = [
    ('gemini-1.5-flash', os.getenv('GEMINI_API_KEY', '')),
    # ('openai:gpt-4o-mini', os.getenv('OPENAI_API_KEY', '')),
    ]


async def main():
    # 優化代碼塊顯示
    prettier_code_blocks()
    console = Console()
    prompt = 'Show me a short example of using Pydantic.'
    console.log(f'詢問: {prompt}...', style='cyan')

    # 遍歷可用模型並流式輸出結果
    for model, api_key in models:
        if api_key:
            console.log(f'使用模型: {model}')
            with Live('', console=console, vertical_overflow='visible') as live:
                async with agent.run_stream(prompt, model=model) as result:
                    async for message in result.stream():
                        # 實時更新 Markdown
                        live.update(Markdown(message))
            console.log(result.usage())  # 輸出模型的使用情況
        else:
            console.log(f'{model} 需要設置對應的 API 密鑰。')


def prettier_code_blocks():
    """讓 rich 的代碼塊更美觀且更易於複製。

    來源: https://github.com/samuelcolvin/aicli/blob/v0.8.0/samuelcolvin_aicli.py#L22
    """

    class SimpleCodeBlock(CodeBlock):
        def __rich_console__(
            self, console: Console, options: ConsoleOptions
        ) -> RenderResult:
            # 去除多餘空格並格式化代碼塊
            code = str(self.text).rstrip()
            yield Text(self.lexer_name, style='dim')  # 顯示語言名稱
            yield Syntax(
                code,
                self.lexer_name,
                theme=self.theme,
                background_color='default',
                word_wrap=True,  # 啟用自動換行
            )
            yield Text(f'/{self.lexer_name}', style='dim')  # 顯示結尾語言名稱

    # 替換 Markdown 中的代碼塊解析方式
    Markdown.elements['fence'] = SimpleCodeBlock


if __name__ == '__main__':
    # 運行主函數
    asyncio.run(main())
