"""HTTP 스트리밍과 MCP 스트리밍을 모두 보여주는 예제 서버."""

# server.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import (
    TextContent
)
import asyncio
import uvicorn
import os

# MCP 서버 생성
mcp = FastMCP("Streamable DEMO")

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "welcome.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

async def event_stream(message: str):
    for i in range(1, 4):
        yield f"Processing file {i}/3...\n"
        await asyncio.sleep(1)
    yield f"Here's the file content: {message}\n"

@app.get("/stream")
async def stream(message: str = "hello"):
    return StreamingResponse(event_stream(message), media_type="text/plain")

@mcp.tool(description="파일 처리 과정을 시뮬레이션하며 진행 알림을 전송하는 도구")
async def process_files(message: str, ctx: Context) -> TextContent:
    files = [f"file_{i}.txt" for i in range(1, 4)]
    for idx, file in enumerate(files, 1):
        await ctx.info(f"Processing {file} ({idx}/{len(files)})...")
        await asyncio.sleep(1)  
    await ctx.info("All files processed!")
    return TextContent(type="text", text=f"Processed files: {', '.join(files)} | Message: {message}")

if __name__ == "__main__":
    import sys
    if "mcp" in sys.argv:
        # streamable-http 전송 방식을 사용하는 MCP 서버 실행
        print("streamable-http 전송 방식을 사용하는 MCP 서버를 시작합니다...")
        # MCP 서버는 /mcp 엔드포인트가 있는 자체 FastAPI 앱을 생성합니다
        mcp.run(transport="streamable-http")
    else:
        # 클래식 HTTP 스트리밍을 위한 FastAPI 서버 실행
        print("클래식 HTTP 스트리밍용 FastAPI 서버를 시작합니다...")
        uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)