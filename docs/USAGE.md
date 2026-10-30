# CLI·MCP 사용 안내

## 설치 없는 CLI

Skill을 어느 경로로 복사했든 해당 폴더의 `tools/clarity.py`를 실행하면 됩니다. 입력 경로는 현재 터미널 위치나 manifest 위치가 아닌 `--root` 기준입니다. 예를 들어 작업 폴더가 `/work/project`라면 `reports/manifest.json` 안의 `src/main.py`도 `/work/project/src/main.py`입니다.

```bash
python3 /path/to/skill/tools/clarity.py audit --root /work/project --original draft-before.md --revised draft-after.md --limit 5
python3 /path/to/skill/tools/clarity.py evidence --root /work/project --manifest manifest.json --limit 5
```

위의 `/path/to/skill`, `/work/project`는 실제 경로로 바꿉니다. 원문과 수정문은 UTF-8 텍스트여야 합니다. 문자열 위치는 1부터 시작하는 Unicode 문자 기준 행·열이며 바이트 위치가 아닙니다. 보고서에 새로 계산한 수치를 추가할 때는 윤문의 사실 보존 검사와 계산 근거 검증을 구분하세요.

Evidence manifest v1 형식은 [로컬 검사 안내](../skills/clarity-wiki/references/local-checks.md), 합성 예시는 [manifest](../skills/clarity-wiki/examples/evidence/manifest.json)를 참고하세요. 이 예시의 기록은 실제 테스트 실행 증거가 아닙니다. 실제 명령·결과와 파일·입력의 SHA-256을 기록한 후 검사합니다. `command`는 문자열로 확인만 하며 실행하지 않습니다.

## MCP 연결

1. 별도 Python 환경에 `python -m pip install '.[mcp]'`로 optional extra를 설치합니다.
2. 호스트가 제공하는 MCP 설정에 Python 실행 파일·런처·작업 폴더의 실제 절대 경로를 지정합니다.
3. 도구 목록이 `audit_revision`, `check_evidence` 두 개인지 확인합니다.

호스트의 서버 설정 JSON 예시입니다. portable `mcp.json`의 `type` 필드와 호스트별 설정 형식은 서로 다를 수 있으므로 제공 환경 안내를 따르세요.

```json
{
  "mcpServers": {
    "clarity-wiki": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": [
        "/absolute/path/to/clarity-wiki/skills/clarity-wiki/tools/mcp_server.py",
        "--root", "/absolute/path/to/workspace"
      ]
    }
  }
}
```

root는 서버 시작 시 고정되고 도구 인자로 바꿀 수 없습니다. MCP 도구 입력은 각각 `{original,revised,limit}` 또는 `{manifest,limit}`입니다. 작업 폴더 밖 입력은 오류로 반환합니다. stdout은 MCP 프로토콜 전용입니다. MCP는 별도 HTTP 서버, 외부 LLM, sampling, 파일 쓰기, 셸 실행 도구를 제공하지 않습니다.

Plugin의 기본 런처는 `--root` 대신 시작 환경의 `CLARITY_WORKSPACE_ROOT`를 읽습니다. 이 값은 **절대 경로**여야 하며 자동으로 홈 디렉터리나 Plugin 디렉터리를 허용하지 않습니다. Plugin을 설치한 호스트에서 환경변수·Python 경로를 지정할 수 없으면 위의 직접 MCP 설정 또는 CLI를 사용합니다.

`python3`에 SDK가 없으면 MCP 시작 시 설치할 extra를 안내합니다. 실제 작업 시간에 무리하게 설치를 반복하지 말고 CLI로 진행할 수 있습니다. 대회에서는 사용이 허용된 설정 탭·터미널만 이용합니다.

## 응답 읽기

- `total_findings`: 전체 검토 후보 수.
- `findings`: `limit`개 이하의 후보와 파일 위치·규칙 코드.
- `truncated`: 전체 후보 중 표시하지 않은 것이 있는지 여부.
- `limitations`: 해당 검사가 판단하지 않는 범위.

감지되지 않는 의미 변경, 인과 단정, 정책 누락은 수동으로 확인해야 합니다. manifest가 검사에 통과해도 사용자 작성 로그의 진실성이나 업무 정답이 인증되지는 않습니다.
