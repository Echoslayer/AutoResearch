"""關於鯨魚的信息 — 一個流式結構化響應驗證的範例。

此腳本從 GPT-4 獲取有關鯨魚的結構化響應，驗證數據，並在數據接收時使用 Rich 動態顯示為表格。

運行指令：

    uv run -m pydantic_ai_examples.stream_whales
"""

from typing import Annotated

import logfire
from pydantic import Field, ValidationError
from rich.console import Console
from rich.live import Live
from rich.table import Table
from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire='BxrGYyHptcKT95hzV30XJqrstPGkd293MvXvrJX8f6XY')


# 定義鯨魚的數據結構
class Whale(TypedDict):
    name: str  # 鯨魚名稱
    length: Annotated[
        float, Field(description='成年鯨魚的平均長度（以米為單位）。')
    ]  # 平均長度
    weight: NotRequired[
        Annotated[
            float,
            Field(description='成年鯨魚的平均重量（以千克為單位）。', ge=50),
        ]
    ]  # 平均重量（可選）
    ocean: NotRequired[str]  # 棲息海洋（可選）
    description: NotRequired[
        Annotated[str, Field(description='簡短描述')]
    ]  # 簡短描述（可選）


# 初始化代理，指定使用 GPT-4 並返回類型為鯨魚列表
agent = Agent('openai:gpt-4o-mini', result_type=list[Whale])


async def main():
    console = Console()  # 初始化 Rich 控制台
    with Live('\n' * 36, console=console) as live:
        # 請求數據
        console.print('請求數據中...', style='cyan')
        async with agent.run_stream(
            'Generate me details of 5 species of Whale.'
        ) as result:
            console.print('響應結果:', style='green')

            # 流式接收結構化響應
            async for message, last in result.stream_structured(debounce_by=0.01):
                try:
                    # 驗證結構化數據
                    whales = await result.validate_structured_result(
                        message, allow_partial=not last
                    )
                except ValidationError as exc:
                    # 忽略缺失字段錯誤
                    if all(
                        e['type'] == 'missing' and e['loc'] == ('response',)
                        for e in exc.errors()
                    ):
                        continue
                    else:
                        raise

                # 創建表格以顯示鯨魚信息
                table = Table(
                    title='鯨魚種類',
                    caption='從 GPT-4 流式接收結構化響應',
                    width=120,
                )
                table.add_column('ID', justify='right')  # 添加 ID 列
                table.add_column('名稱')  # 添加名稱列
                table.add_column('平均長度 (m)', justify='right')  # 添加平均長度列
                table.add_column('平均重量 (kg)', justify='right')  # 添加平均重量列
                table.add_column('棲息海洋')  # 添加棲息海洋列
                table.add_column('描述', justify='right')  # 添加描述列

                # 填充表格數據
                for wid, whale in enumerate(whales, start=1):
                    table.add_row(
                        str(wid),
                        whale['name'],  # 鯨魚名稱
                        f'{whale["length"]:0.0f}',  # 平均長度
                        f'{w:0.0f}' if (w := whale.get('weight')) else '…',  # 平均重量
                        whale.get('ocean') or '…',  # 棲息海洋
                        whale.get('description') or '…',  # 描述
                    )
                # 更新表格顯示
                live.update(table)


if __name__ == '__main__':
    import asyncio

    # 運行主函數
    asyncio.run(main())
