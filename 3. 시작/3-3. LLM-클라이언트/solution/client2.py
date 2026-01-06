"""MCP 클라이언트 예제

이 클라이언트는 다음과 같은 흐름으로 동작합니다:
1. MCP 서버(server.py)에 연결
2. 서버로부터 사용 가능한 도구(tools) 목록 가져오기
3. 사용자 질문을 Azure AI LLM에게 전달 (도구 정보 포함)
4. LLM이 필요한 도구를 선택하고 매개변수 결정
5. 선택된 도구를 MCP 서버에서 실행
6. 결과 출력
"""

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# LLM 관련 라이브러리 임포트
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import json

# ========== 1단계: MCP 서버 연결 설정 ==========
# stdio 연결에 사용할 서버 파라미터 생성
# MCP 서버를 subprocess로 실행하고 stdin/stdout으로 통신
server_params = StdioServerParameters(
    command="mcp",  # 실행할 명령어 (mcp CLI)
    args=["run", "server.py"],  # server.py를 실행하도록 인수 전달
    env=None,  # 선택적 환경 변수
)

# ========== 3단계: Azure AI LLM 호출 ==========
def call_llm(prompt, functions):
    """사용자 질문과 사용 가능한 도구 목록을 LLM에게 전달
    
    Args:
        prompt: 사용자 질문 (예: "20에 2를 더해줘")
        functions: MCP 서버에서 제공하는 도구 목록 (JSON 스키마 형식)
        
    Returns:
        LLM이 선택한 도구 호출 목록 [{ "name": "add", "args": {"a": 20, "b": 2} }]
    """
    # Azure AI Foundry 설정
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
        # Azure AI에게 질문과 함께 사용 가능한 도구 목록(functions) 전달
        # LLM은 질문을 이해하고 적절한 도구를 선택함
        response = client.complete(
            messages=[
                {
                "role": "system",
                "content": "You are a helpful assistant.",
                },
                {
                "role": "user",
                "content": prompt,  # "20에 2를 더해줘"
                },
            ],
            model=model_name,
            tools=functions,  # 중요! MCP 서버의 도구 목록을 LLM에게 알려줌
            # 선택적 매개변수
            temperature=1.0,
            max_tokens=1000,
            top_p=1.0    
        )

        response_message = response.choices[0].message
        
        functions_to_call = []

        # LLM이 도구 호출을 제안했는지 확인
        if response_message.tool_calls:
            print("\nLLM이 다음 도구 호출을 제안했습니다:")
            for tool_call in response_message.tool_calls:
                print(f"   - 도구: {tool_call.function.name}")
                print(f"   - 인수: {tool_call.function.arguments}")
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                functions_to_call.append({ "name": name, "args": args })

        return functions_to_call
        
    except Exception as e:
        print(f"LLM 호출 중 오류 발생: {e}")
        return []

def convert_to_llm_tool(tool):
    """MCP 도구 스키마를 Azure AI가 이해할 수 있는 형식으로 변환
    
    MCP 서버의 도구 정보를 Azure AI의 Function Calling 형식으로 변환합니다.
    예: add(a: int, b: int) -> {"type": "function", "function": {"name": "add", ...}}
    """
    tool_schema = {
        "type": "function",
        "function": {
            "name": tool.name,  # 도구 이름 (예: "add")
            "description": tool.description,  # 도구 설명 (LLM이 이를 읽고 언제 사용할지 결정)
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema.get("properties", {}),  # 입력 매개변수 정의
                "required": tool.inputSchema.get("required", [])  # 필수 매개변수 목록
            }
        }
    }

    return tool_schema

async def run():
    """메인 실행 함수 - MCP 클라이언트의 전체 워크플로우"""
    
    print("="*60)
    print("MCP 클라이언트 시작")
    print("="*60)
    
    # MCP 서버와 stdio 연결 수립
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # ========== 2단계: MCP 서버 초기화 및 기능 탐색 ==========
            print("\n[1단계] MCP 서버에 연결 중...")
            await session.initialize()
            print("서버 연결 성공!\n")

            # 사용 가능한 리소스 목록 조회 (예: 인사말 템플릿 등)
            print("[2단계] 서버의 리소스 탐색 중...")
            resources = await session.list_resources()
            for resource in resources:
                print(f"  리소스: {resource}")

            # 사용 가능한 도구 목록 조회 (예: add, subtract 등)
            print("\n[3단계] 서버의 도구 탐색 중...")
            tools = await session.list_tools()

            functions = []  # Azure AI에게 전달할 도구 목록

            for tool in tools.tools:
                print(f"  도구 발견: {tool.name} - {tool.description}")
                # MCP 도구 스키마를 Azure AI 형식으로 변환
                functions.append(convert_to_llm_tool(tool))
            
            # ========== 4단계: 사용자 질문 처리 ==========
            prompt = "20에 2를 더해줘"
            print(f"\n[4단계] 사용자 질문: '{prompt}'")

            # LLM에게 질문하고 어떤 도구를 사용할지 결정받기
            functions_to_call = call_llm(prompt, functions)

            # ========== 5단계: 도구 실행 ==========
            if functions_to_call:
                print("\n[5단계] MCP 서버에서 도구 실행 중...")
                for f in functions_to_call:
                    print(f"\n  실행: {f['name']}({f['args']})")
                    # MCP 서버의 도구를 실제로 호출
                    result = await session.call_tool(f["name"], arguments=f["args"])
                    print(f"  결과: {result.content}")
            else:
                print("\nLLM이 도구를 호출하지 않았습니다.")
            
            print("\n" + "="*60)
            print("완료!")
            print("="*60)


if __name__ == "__main__":
    import asyncio
    # 환경 변수 설정 예시 (실제 실행 시에는 시스템 환경 변수에 설정하는 것이 좋습니다)
    # os.environ["AZURE_INFERENCE_ENDPOINT"] = "https://<your-endpoint>.models.ai.azure.com"
    # os.environ["AZURE_INFERENCE_CREDENTIAL"] = "<your-key>"
    # os.environ["AZURE_INFERENCE_MODEL"] = "gpt-4o"
    
    asyncio.run(run())