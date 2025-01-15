"""使用 PydanticAI 從文字輸入構建 Pydantic 模型的簡單範例。

運行指令：

    uv run -m pydantic_ai_examples.pydantic_model
"""

import os
from typing import cast

import logfire
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire='if-token-present')


class MyModel(BaseModel):
    """定義一個包含城市和國家的 Pydantic 模型。"""
    city: str  # 城市名稱
    country: str  # 國家名稱


# 獲取環境變量中的模型名稱，默認為 'openai:gpt-4o'
model = cast(KnownModelName, os.getenv('PYDANTIC_AI_MODEL', 'deepseek'))
print(f'使用的模型: {model}')

# 初始化代理，並指定返回類型為 MyModel
agent = Agent(model, result_type=MyModel)

if __name__ == '__main__':
    # 使用代理同步運行，解析輸入文字
    result = agent.run_sync('The windy city in the US of A.')
    # 輸出解析結果
    print(result.data)
    # 輸出使用情況
    print(result.usage())
