#!/usr/bin/env python3
"""MCP stdio 서버 예제 (MCP 사양 2025-06-18 기준).

더 이상 사용이 권장되지 않는 SSE 대신, 권장되는 stdio 전송 방식을
사용하는 MCP 서버 예제입니다. stdio 전송 방식은 더 간단하고,
더 안전하며, 성능도 우수합니다.
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 로깅 설정 (stdio 서버에서는 stdout이 아닌 stderr를 사용해야 합니다)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 서버 인스턴스 생성
server = Server("example-stdio-server")

# list_tools 및 call_tool 핸들러를 사용해 도구를 정의
@server.list_tools()
async def list_tools() -> list[Tool]:
    """서버에서 제공하는 도구 목록을 반환합니다."""
    return [
        Tool(
            name="add",
            description="두 숫자의 합을 계산합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "첫 번째 숫자"},
                    "b": {"type": "number", "description": "두 번째 숫자"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="multiply",
            description="두 숫자의 곱을 계산합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "첫 번째 숫자"},
                    "b": {"type": "number", "description": "두 번째 숫자"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="get_greeting",
            description="이름을 받아 개인화된 인사말을 생성합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "인사할 대상의 이름"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_server_info",
            description="이 MCP 서버에 대한 정보를 가져옵니다.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 호출을 처리합니다."""
    if name == "add":
        result = arguments["a"] + arguments["b"]
        logger.info(f"Adding {arguments['a']} + {arguments['b']} = {result}")
        return [TextContent(type="text", text=str(result))]
    
    elif name == "multiply":
        result = arguments["a"] * arguments["b"]
        logger.info(f"Multiplying {arguments['a']} * {arguments['b']} = {result}")
        return [TextContent(type="text", text=str(result))]
    
    elif name == "get_greeting":
        greeting = f"Hello, {arguments['name']}! MCP stdio 서버에 오신 것을 환영합니다."
        logger.info(f"{arguments['name']}에 대한 인사말 생성")
        return [TextContent(type="text", text=greeting)]
    
    elif name == "get_server_info":
        info = {
            "server_name": "example-stdio-server",
            "version": "1.0.0",
            "transport": "stdio",
            "capabilities": ["tools"],
            "description": "stdio 전송 방식을 사용하는 예제 MCP 서버 (MCP 2025-06-18 사양 기준)"
        }
        return [TextContent(type="text", text=str(info))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """stdio 전송 방식을 사용하는 메인 서버 함수."""
    logger.info("MCP stdio 서버를 시작합니다...")
    
    try:
        # 권장되는 stdio 전송 방식을 사용합니다
        async with stdio_server() as (read_stream, write_stream):
            logger.info("stdio 전송 방식으로 서버가 연결되었습니다")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"서버 오류: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())