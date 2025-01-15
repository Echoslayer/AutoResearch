"""多代理流程範例，其中一個代理將工作委派給另一個代理。

在此情境中，一組代理合作為用戶尋找航班。
"""

import datetime
from dataclasses import dataclass
from typing import Literal

import logfire
from pydantic import BaseModel, Field
from rich.prompt import Prompt

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import Usage, UsageLimits

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire='if-token-present')


class FlightDetails(BaseModel):
    """最適合的航班詳情。"""

    flight_number: str  # 航班號
    price: int  # 價格
    origin: str = Field(description='三字母機場代碼')  # 起點
    destination: str = Field(description='三字母機場代碼')  # 終點
    date: datetime.date  # 日期


class NoFlightFound(BaseModel):
    """當未找到有效航班時的情況。"""


@dataclass
class Deps:
    web_page_text: str  # 網頁文字
    req_origin: str  # 請求的起點
    req_destination: str  # 請求的終點
    req_date: datetime.date  # 請求的日期


# 負責控制對話流程的代理
search_agent = Agent[Deps, FlightDetails | NoFlightFound](
    'openai:gpt-4o',
    result_type=FlightDetails | NoFlightFound,  # 返回的結果類型
    retries=4,  # 重試次數
    system_prompt=(
        '您的工作是為用戶找到指定日期最便宜的航班。'
    ),
)


# 負責從網頁文字中提取航班詳情的代理
extraction_agent = Agent(
    'openai:gpt-4o',
    result_type=list[FlightDetails],
    system_prompt='從給定的文字中提取所有航班的詳情。',
)


@search_agent.tool
async def extract_flights(ctx: RunContext[Deps]) -> list[FlightDetails]:
    """獲取所有航班詳情。"""
    # 傳遞使用量到搜索代理，以便統計請求
    result = await extraction_agent.run(ctx.deps.web_page_text, usage=ctx.usage)
    logfire.info('找到 {flight_count} 個航班', flight_count=len(result.data))
    return result.data


@search_agent.result_validator
async def validate_result(
    ctx: RunContext[Deps], result: FlightDetails | NoFlightFound
) -> FlightDetails | NoFlightFound:
    """程序化驗證航班是否符合條件。"""
    if isinstance(result, NoFlightFound):
        return result

    errors: list[str] = []
    if result.origin != ctx.deps.req_origin:
        errors.append(
            f'航班起點應為 {ctx.deps.req_origin}，而非 {result.origin}'
        )
    if result.destination != ctx.deps.req_destination:
        errors.append(
            f'航班終點應為 {ctx.deps.req_destination}，而非 {result.destination}'
        )
    if result.date != ctx.deps.req_date:
        errors.append(f'航班日期應為 {ctx.deps.req_date}，而非 {result.date}')

    if errors:
        raise ModelRetry('\n'.join(errors))
    else:
        return result


class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)  # 排號，限制範圍 1-30
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']  # 座位字母


class Failed(BaseModel):
    """無法提取座位選擇。"""


# 負責提取用戶座位選擇的代理
seat_preference_agent = Agent[
    None, SeatPreference | Failed
](
    'openai:gpt-4o',
    result_type=SeatPreference | Failed,  # 返回座位選擇或失敗
    system_prompt=(
        "提取用戶的座位偏好。"
        "座位 A 和 F 是靠窗座位。"
        "第 1 排是前排，提供額外的腿部空間。"
        "第 14 和 20 排也有額外的腿部空間。"
    ),
)


# 實際情況下，這些數據可能是從預訂網站下載的
flights_web_page = """
1. 航班 SFO-AK123
- 價格: $350
- 起點: San Francisco International Airport (SFO)
- 終點: Ted Stevens Anchorage International Airport (ANC)
- 日期: 2025 年 1 月 10 日
...
"""

# 限制應用對 LLM 的請求數量
usage_limits = UsageLimits(request_limit=15)


async def main():
    deps = Deps(
        web_page_text=flights_web_page,
        req_origin='SFO',
        req_destination='ANC',
        req_date=datetime.date(2025, 1, 10),
    )
    message_history: list[ModelMessage] | None = None
    usage: Usage = Usage()
    # 運行代理直到找到滿意的航班
    while True:
        result = await search_agent.run(
            f'幫我找到從 {deps.req_origin} 飛往 {deps.req_destination} 的航班，日期為 {deps.req_date}',
            deps=deps,
            usage=usage,
            message_history=message_history,
            usage_limits=usage_limits,
        )
        if isinstance(result.data, NoFlightFound):
            print('未找到航班')
            break
        else:
            flight = result.data
            print(f'找到航班: {flight}')
            answer = Prompt.ask(
                '您想購買這趟航班嗎？還是繼續搜尋？(buy/*search)',
                choices=['buy', 'search', ''],
                show_choices=False,
            )
            if answer == 'buy':
                seat = await find_seat(usage)
                await buy_tickets(flight, seat)
                break
            else:
                message_history = result.all_messages(
                    result_tool_return_content='請建議其他航班'
                )


async def find_seat(usage: Usage) -> SeatPreference:
    """尋找用戶座位偏好。"""
    message_history: list[ModelMessage] | None = None
    while True:
        answer = Prompt.ask('您希望選擇哪個座位？')

        result = await seat_preference_agent.run(
            answer,
            message_history=message_history,
            usage=usage,
            usage_limits=usage_limits,
        )
        if isinstance(result.data, SeatPreference):
            return result.data
        else:
            print('無法理解座位偏好。請重試。')
            message_history = result.all_messages()


async def buy_tickets(flight_details: FlightDetails, seat: SeatPreference):
    """購買航班票。"""
    print(f'正在購買航班 {flight_details=!r} 和座位 {seat=!r}...')


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
