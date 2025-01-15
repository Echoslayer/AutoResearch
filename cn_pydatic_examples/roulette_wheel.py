"""範例展示如何使用 PydanticAI 創建一個簡單的輪盤賭遊戲。

運行指令:
    uv run -m pydantic_ai_examples.roulette_wheel
"""

from __future__ import annotations as _annotations

import asyncio
from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext


import logfire

# 配置 logfire（這裡使用範例令牌）
logfire.configure()


# 定義依賴類
@dataclass
class Deps:
    winning_number: int  # 中獎號碼


# 創建輪盤賭代理，設置類型、重試次數及結果類型
roulette_agent = Agent(
    'openai:gpt-4o-mini',  # 使用的模型名稱
    deps_type=Deps,  # 指定依賴類型
    retries=3,  # 最大重試次數
    result_type=bool,  # 返回結果類型
    system_prompt=(
        '使用 `roulette_wheel` 函數來判斷玩家是否根據下注號碼獲勝。'
    ),
)


@roulette_agent.tool
async def roulette_wheel(
    ctx: RunContext[Deps], square: int
) -> Literal['winner', 'loser']:
    """檢查下注的號碼是否中獎。

    參數:
        ctx: 包含中獎號碼的上下文。
        square: 玩家下注的號碼。
    """
    return 'winner' if square == ctx.deps.winning_number else 'loser'


async def main():
    # 設置依賴項（中獎號碼為 18）
    winning_number = 18
    deps = Deps(winning_number=winning_number)

    # 使用代理運行範例下注，並以流方式處理
    async with roulette_agent.run_stream(
        'Put my money on square eighteen', deps=deps
    ) as response:
        # 獲取結果並打印
        result = await response.get_data()
        print('下注 18:', result)

    async with roulette_agent.run_stream(
        'I bet five is the winner', deps=deps
    ) as response:
        # 獲取結果並打印
        result = await response.get_data()
        print('下注 5:', result)


if __name__ == '__main__':
    # 運行主函數
    asyncio.run(main())
