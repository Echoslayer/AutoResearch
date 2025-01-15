"""使用 PydanticAI 建立銀行支援代理的完整範例。

運行指令：

    uv run -m pydantic_ai_examples.bank_support
"""

from dataclasses import dataclass

from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext


class DatabaseConn:
    """這是一個用於範例的假資料庫。

    在實際應用中，您會連接到外部資料庫（例如 PostgreSQL）
    以獲取有關客戶的資訊。
    """

    @classmethod
    async def customer_name(cls, *, id: int) -> str | None:
        # 模擬查詢客戶名稱
        if id == 123:
            return 'John'

    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        # 模擬查詢客戶餘額
        if id == 123:
            return 123.45
        else:
            raise ValueError('未找到客戶')


@dataclass
class SupportDependencies:
    # 支援代理所需的依賴
    customer_id: int  # 客戶 ID
    db: DatabaseConn  # 資料庫連接物件


class SupportResult(BaseModel):
    # 定義支援結果的資料模型
    support_advice: str = Field(description='提供給客戶的建議')
    block_card: bool = Field(description='是否需要封鎖信用卡')
    risk: int = Field(description='查詢的風險等級', ge=0, le=10)


# 初始化支援代理
support_agent = Agent(
    'openai:gpt-4o-mini',  # 使用 OpenAI GPT-4o 作為基礎模型
    deps_type=SupportDependencies,  # 指定依賴類型
    result_type=SupportResult,  # 指定結果類型
    system_prompt=(
        '您是我們銀行的支援代理，請為客戶提供支援並評估其查詢的風險等級。'
        "使用客戶的姓名進行回覆。"
    ),
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    # 添加客戶名稱到系統提示中
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"客戶的姓名是 {customer_name!r}"


@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> str:
    """返回客戶的當前賬戶餘額。"""
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return f'${balance:.2f}'


if __name__ == '__main__':
    # 設置依賴參數
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    # 使用代理處理客戶的查詢
    result = support_agent.run_sync('What is my balance?', deps=deps)
    print(result.data)
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = support_agent.run_sync('I just lost my card!', deps=deps)
    print(result.data)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """
