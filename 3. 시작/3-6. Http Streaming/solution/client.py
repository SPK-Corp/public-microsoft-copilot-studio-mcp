# client.py
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import asyncio
import mcp.types as types
from mcp.shared.session import RequestResponder
import requests
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mcp_client')

class LoggingCollector:
    def __init__(self):
        self.log_messages: list[types.LoggingMessageNotificationParams] = []
    async def __call__(self, params: types.LoggingMessageNotificationParams) -> None:
        self.log_messages.append(params)
        logger.info("MCP 로그: %s - %s", params.level, params.data)

logging_collector = LoggingCollector()
port = 8000

async def message_handler(
    message: RequestResponder[types.ServerRequest, types.ClientResult]
    | types.ServerNotification
    | Exception,
) -> None:
    logger.info("메시지 수신: %s", message)
    if isinstance(message, Exception):
        logger.error("예외가 발생했습니다!")
        raise message
    elif isinstance(message, types.ServerNotification):
        logger.info("알림: %s", message)
    elif isinstance(message, RequestResponder):
        logger.info("요청 처리기: %s", message)
    else:
        logger.info("서버 메시지: %s", message)

async def main():
    logger.info("클라이언트를 시작합니다...")
    async with streamablehttp_client(f"http://localhost:{port}/mcp") as (
        read_stream,
        write_stream,
        session_callback,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
            logging_callback=logging_collector,
            message_handler=message_handler,
        ) as session:
            id_before = session_callback()
            logger.info("초기화 전 세션 ID: %s", id_before)
            await session.initialize()
            id_after = session_callback()
            logger.info("초기화 후 세션 ID: %s", id_after)
            logger.info("세션 초기화 완료, 도구 호출 준비 완료.")
            tool_result = await session.call_tool("process_files", {"message": "hello from client"})
            logger.info("도구 결과: %s", tool_result)
            if logging_collector.log_messages:
                logger.info("수집된 로그 메시지:")
                for log in logging_collector.log_messages:
                    logger.info("로그: %s", log)

def stream_progress(message="hello", url="http://localhost:8000/stream"):
    params = {"message": message}
    logger.info("메시지 %s로 %s 에 연결 중", message, url)
    try:
        with requests.get(url, params=params, stream=True, timeout=10) as r:
            r.raise_for_status()
            logger.info("--- 스트리밍 진행 상황 ---")
            for line in r.iter_lines():
                if line:
                    # 스트리밍된 내용을 눈으로 확인할 수 있도록 stdout에 출력
                    decoded_line = line.decode().strip()
                    print(decoded_line)
                    logger.debug("스트림 내용: %s", decoded_line)
            logger.info("--- 스트리밍 종료 ---")
    except requests.RequestException as e:
        logger.error("스트리밍 중 오류 발생: %s", e)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        # MCP 클라이언트 모드
        logger.info("MCP 클라이언트를 실행합니다...")
        asyncio.run(main())
    else:
        # 클래식 HTTP 스트리밍 클라이언트 모드
        logger.info("클래식 HTTP 스트리밍 클라이언트를 실행합니다...")
        stream_progress()
        
    # 기본적으로 두 모드를 모두 실행하지 않고, 사용자가 모드를 선택하도록 합니다.