"""클라이언트 예제에서 사용할 간단한 MCP 서버."""

# server.py
from mcp.server.fastmcp import FastMCP

# MCP 서버 인스턴스 생성
mcp = FastMCP("Demo")


# 덧셈 도구 추가
@mcp.tool()
def add(a: int, b: int) -> int:
    """두 숫자의 합을 계산합니다."""
    return a + b


# 동적 인사말 리소스 추가
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """이름을 받아 개인화된 인사말을 반환합니다."""
    return f"Hello, {name}!"
