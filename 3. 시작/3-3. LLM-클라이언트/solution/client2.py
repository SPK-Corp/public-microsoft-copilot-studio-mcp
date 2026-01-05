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
    # Azure AI Foundry 설정
    # 환경 변수에서 엔드포인트와 키를 가져옵니다.
    # Azure AI Studio > Project > Management > Endpoints 에서 확인 가능
    # 예: https://<your-resource-name>.services.ai.azure.com/models
    endpoint = "https://aifondry-workshop-demo.services.ai.azure.com/models"
    key = ""
    
    # 배포된 모델 이름 (Azure AI Foundry에서 배포한 모델명, 예: gpt-4o)
    model_name = os.environ.get("AZURE_INFERENCE_MODEL", "gpt-4o")

    if not endpoint or not key:
        print("경고: AZURE_INFERENCE_ENDPOINT 또는 AZURE_INFERENCE_CREDENTIAL 환경 변수가 설정되지 않았습니다.")
        # 테스트를 위해 기존 GitHub Models 설정으로 폴백(Fallback)하거나 에러를 발생시킬 수 있습니다.
        # 여기서는 에러를 방지하기 위해 예시 값을 넣거나 리턴합니다.
        return []

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    print(f"LLM 호출 중 (Model: {model_name})")
    try:
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
            tools=functions,
            # 선택적 매개변수
            temperature=1.0,
            max_tokens=1000,
            top_p=1.0    
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
        
    except Exception as e:
        print(f"LLM 호출 중 오류 발생: {e}")
        return []

def convert_to_llm_tool(tool):
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema.get("properties", {}),
                "required": tool.inputSchema.get("required", [])
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
                # print("도구 스키마", tool.inputSchema)
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
    # 환경 변수 설정 예시 (실제 실행 시에는 시스템 환경 변수에 설정하는 것이 좋습니다)
    # os.environ["AZURE_INFERENCE_ENDPOINT"] = "https://<your-endpoint>.models.ai.azure.com"
    # os.environ["AZURE_INFERENCE_CREDENTIAL"] = "<your-key>"
    # os.environ["AZURE_INFERENCE_MODEL"] = "gpt-4o"
    
    asyncio.run(run())