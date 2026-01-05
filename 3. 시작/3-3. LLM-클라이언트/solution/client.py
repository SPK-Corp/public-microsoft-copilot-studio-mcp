from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# LLM 관련 라이브러리 임포트
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import json

# stdio 연결에 사용할 서버 파라미터 생성
server_params = StdioServerParameters(
    command="mcp",  # 실행할 명령어
    args=["run", "server.py"],  # 선택적 커맨드 라인 인수
    env=None,  # 선택적 환경 변수
)

def call_llm(prompt, functions):
    token = os.environ["GITHUB_TOKEN"]
    endpoint = "https://models.inference.ai.azure.com"

    model_name = "gpt-4o"

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    print("LLM 호출 중")
    response = client.complete(
        messages=[
            {
            "role": "system",
            "content": "You are a helpful assistant.",
            },
            {
            "role": "user",
            "content": prompt,
            },
        ],
        model=model_name,
        tools = functions,
        # 선택적 매개변수
        temperature=1.,
        max_tokens=1000,
        top_p=1.    
    )

    response_message = response.choices[0].message
    
    functions_to_call = []

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            print("TOOL: ", tool_call)
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            functions_to_call.append({ "name": name, "args": args })

    return functions_to_call

def convert_to_llm_tool(tool):
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "type": "function",
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema["properties"]
            }
        }
    }

    return tool_schema

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

            functions = []

            for tool in tools.tools:
                print("도구: ", tool.name)
                print("도구 스키마", tool.inputSchema["properties"])
                functions.append(convert_to_llm_tool(tool))
            
            prompt = "20에 2를 더해줘"

            # LLM에게 어떤 도구를 호출할지(필요하다면) 묻기
            functions_to_call = call_llm(prompt, functions)

            # 제안된 도구들을 실제로 호출
            for f in functions_to_call:
                result = await session.call_tool(f["name"], arguments=f["args"])
                print("도구 결과: ", result.content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())


