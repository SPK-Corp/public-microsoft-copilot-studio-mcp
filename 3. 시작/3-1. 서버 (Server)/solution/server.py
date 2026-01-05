# server.py
from mcp.server.fastmcp import FastMCP

"""간단한 MCP 서버 예제.

덧셈/뺄셈 도구와 이름 기반 인사 리소스를 제공합니다.
"""

# MCP 서버 인스턴스 생성
mcp = FastMCP("Demo")


# 덧셈 도구 추가
@mcp.tool()
def add(a: int, b: int) -> int:
    """두 숫자의 합을 계산합니다."""
    return a + b
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """두 숫자의 차이를 계산합니다."""
    return a - b

# 동적 인사말 리소스 추가
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """이름을 받아 개인화된 인사말을 반환합니다."""
    return f"Hello, {name}!"


# 메인 실행 블록 - 서버를 실행하기 위해 필요합니다
if __name__ == "__main__":
    mcp.run()