"""PydanticAI 範例，展示如何使用多個工具讓 LLM 依次調用以回答問題。

此範例是一個“天氣”代理，允許用戶查詢多個城市的天氣。
代理會先使用 `get_lat_lng` 工具獲取位置的緯度和經度，然後使用
`get_weather` 工具獲取天氣。

運行指令：

    uv run -m pydantic_ai_examples.weather_agent
"""

from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import logfire
from devtools import debug
from httpx import AsyncClient

from pydantic_ai import Agent, ModelRetry, RunContext

# 如果未配置 logfire，則不會發送任何內容，僅作為範例使用
logfire.configure(send_to_logfire=os.getenv('LOGFIRE_API_KEY', ''))


@dataclass
class Deps:
    """依賴類型，包含 HTTP 客戶端和 API 密鑰。"""
    client: AsyncClient  # HTTP 客戶端
    weather_api_key: str | None  # 天氣 API 密鑰
    geo_api_key: str | None  # 地理編碼 API 密鑰


# 創建天氣代理
weather_agent = Agent(
    'openai:gpt-4o-mini',
    # 為某些模型提供指導性提示以正確使用工具
    system_prompt=(
        '簡明回答，每次用一句話。'
        '使用 `get_lat_lng` 工具獲取位置的緯度和經度，'
        '然後使用 `get_weather` 工具獲取天氣信息。'
    ),
    deps_type=Deps,
    retries=2,  # 最大重試次數
)


@weather_agent.tool
async def get_lat_lng(
    ctx: RunContext[Deps], location_description: str
) -> dict[str, float]:
    """獲取位置的緯度和經度。

    參數:
        ctx: 上下文，包含依賴信息。
        location_description: 位置描述。
    """
    if ctx.deps.geo_api_key is None:
        # 如果未提供 API 密鑰，返回預設數據（倫敦）
        return {'lat': 51.1, 'lng': -0.1}

    params = {
        'q': location_description,
        'api_key': ctx.deps.geo_api_key,
    }
    with logfire.span('調用地理編碼 API', params=params) as span:
        r = await ctx.deps.client.get('https://geocode.maps.co/search', params=params)
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

    if data:
        return {'lat': data[0]['lat'], 'lng': data[0]['lon']}
    else:
        raise ModelRetry('無法找到該位置')


@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """獲取指定位置的天氣。

    參數:
        ctx: 上下文，包含依賴信息。
        lat: 緯度。
        lng: 經度。
    """
    if ctx.deps.weather_api_key is None:
        # 如果未提供 API 密鑰，返回預設天氣信息
        return {'temperature': '21 °C', 'description': 'Sunny'}

    params = {
        'apikey': ctx.deps.weather_api_key,
        'location': f'{lat},{lng}',
        'units': 'metric',
    }
    with logfire.span('調用天氣 API', params=params) as span:
        r = await ctx.deps.client.get(
            'https://api.tomorrow.io/v4/weather/realtime', params=params
        )
        r.raise_for_status()
        data = r.json()
        span.set_attribute('response', data)

    values = data['data']['values']
    # 天氣代碼對應的描述
    code_lookup = {
        1000: 'Clear, Sunny',
        1100: 'Mostly Clear',
        1101: 'Partly Cloudy',
        1102: 'Mostly Cloudy',
        1001: 'Cloudy',
        2000: 'Fog',
        2100: 'Light Fog',
        4000: 'Drizzle',
        4001: 'Rain',
        4200: 'Light Rain',
        4201: 'Heavy Rain',
        5000: 'Snow',
        5001: 'Flurries',
        5100: 'Light Snow',
        5101: 'Heavy Snow',
        6000: 'Freezing Drizzle',
        6001: 'Freezing Rain',
        6200: 'Light Freezing Rain',
        6201: 'Heavy Freezing Rain',
        7000: 'Ice Pellets',
        7101: 'Heavy Ice Pellets',
        7102: 'Light Ice Pellets',
        8000: 'Thunderstorm',
    }
    return {
        'temperature': f'{values["temperatureApparent"]:0.0f}°C',
        'description': code_lookup.get(values['weatherCode'], 'Unknown'),
    }


async def main():
    async with AsyncClient() as client:
        # 設置 API 密鑰
        weather_api_key = os.getenv('WEATHER_API_KEY')  # 天氣 API 密鑰
        geo_api_key = os.getenv('GEO_API_KEY')  # 地理編碼 API 密鑰
        deps = Deps(
            client=client, weather_api_key=weather_api_key, geo_api_key=geo_api_key
        )
        # 使用代理查詢天氣
        result = await weather_agent.run(
            'What is the weather like in London and in Wiltshire?', deps=deps
        )
        debug(result)  # 調試輸出
        print('回應:', result.data)


if __name__ == '__main__':
    # 運行主函數
    asyncio.run(main())
