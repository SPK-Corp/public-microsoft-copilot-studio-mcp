from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# stdio 연결에 사용할 서버 파라미터 생성
server_params = StdioServerParameters(
    command="mcp",  # 실행할 명령어
    args=["run", "server.py"],  # 선택적 커맨드 라인 인수
    env=None,  # 선택적 환경 변수
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # 연결 초기화
            await session.initialize()

            # 사용 가능한 리소스 목록 조회
            resources = await session.list_resources()
            print("리소스 목록 조회")
            for resource in resources:
                print("리소스: ", resource)

            # 사용 가능한 도구 목록 조회
            tools = await session.list_tools()
            print("도구 목록 조회")
            for tool in tools.tools:
                print("도구: ", tool.name)

            # 리소스 읽기
            print("리소스 읽기")
            content, mime_type = await session.read_resource("greeting://hello")

            # 도구 호출
            print("도구 호출")
            result = await session.call_tool("add", arguments={"a": 1, "b": 7})
            print(result.content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())