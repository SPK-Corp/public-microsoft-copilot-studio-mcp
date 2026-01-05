# 이 샘플 실행하기

`uv` 설치를 권장하지만 필수는 아닙니다. 자세한 내용은 [instructions](https://docs.astral.sh/uv/#highlights)를 참고하세요.

## -0- 가상 환경 만들기

```bash
python -m venv venv
```

## -1- 가상 환경 활성화하기

```bash
venv\Scrips\activate
```

## -2- 의존성 설치하기

```bash
pip install "mcp[cli]"
pip install openai
pip install azure-ai-inference
pip install azure-core
```

## -3- 샘플 실행하기

```bash
python client.py
```

다음과 비슷한 출력이 나타날 것입니다:

```text
LISTING RESOURCES
Resource:  ('meta', None)
Resource:  ('nextCursor', None)
Resource:  ('resources', [])
                    INFO     Processing request of type ListToolsRequest                                                                               server.py:534
LISTING TOOLS
Tool:  add
Tool {'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
CALLING LLM
TOOL:  {'function': {'arguments': '{"a":2,"b":20}', 'name': 'add'}, 'id': 'call_BCbyoCcMgq0jDwR8AuAF9QY3', 'type': 'function'}
[05/08/25 21:04:55] INFO     Processing request of type CallToolRequest                                                                                server.py:534
TOOLS result:  [TextContent(type='text', text='22', annotations=None)]
```
