# Clarity Wiki 사전 체험 빠른 시작

갱신일: 2026-10-30 (Asia/Seoul). 사전 체험에서 설치하고 정상 작동을 확인하는 순서다. **감독 앱·촬영 연결을 먼저 확인한 뒤 Skill과 CLI를 점검한다.** MCP는 시간이 남을 때 [5번의 선택 연결](#5-선택-로컬-mcp-연결)을 확인한다.

필요 환경은 Git, Python 3.10 이상, POSIX 파일 읽기를 지원하는 macOS/Linux다. 제공 Codex는 업데이트하지 않으며 개인 계정·API 키를 연결하지 않는다. 이 문서는 [시험 환경 프로필](skills/clarity-wiki/references/shared/exam-boundaries.md)의 운영 메일·기존 가이드 제한을 함께 따른다.

## 0. Skill·MCP 한 번에 설치

둘 다 설치하고 MCP 호출까지 자동 점검하려면 웹 IDE의 **과제 작업 폴더**에서 아래 블록을 실행한다. Skill만 먼저 확인하려면 1번의 수동 설치를 사용한다.

```bash
CW_SETUP_SRC="$(mktemp -d)" &&
git clone --depth 1 --quiet https://github.com/dailykim149656-source/clarity-wiki.git "$CW_SETUP_SRC" &&
python3 "$CW_SETUP_SRC/tools/install.py" --root "$PWD" --check
```

이미 이 저장소를 내려받았다면 같은 작업 폴더에서 `python3 /저장소의/절대경로/tools/install.py --root "$PWD" --check`로 실행할 수도 있다. `--root`를 생략하면 현재 폴더에 설치한다. `--check`를 생략하면 설치·구조 검사·연결 JSON 출력까지만 진행한다.

설치 스크립트는 다음 작업을 순서대로 수행한다.

1. 과제 폴더의 `.agents/skills/clarity-wiki`에 공개 Skill을 복사한다.
2. 그 안의 `.venv`에 공식 MCP SDK `1.30.0`을 설치한다.
3. SDK import·버전과 Skill 구조를 확인한다.
4. `--check`가 있으면 임시 합성 파일로 서버 초기화·도구 목록·`audit_revision`·`check_evidence`를 실제 MCP stdio로 점검하고 파일을 정리한다.
5. 실제 절대 경로가 들어간 `mcpServers` 연결 JSON을 출력한다.

진행 로그와 점검 보고서는 **stderr**, 성공한 연결 JSON만 **stdout**으로 출력한다. 성공 시 종료 코드는 `0`, 설치·점검 실패 시 `2`이며 실패하면 연결 JSON을 출력하지 않는다. SDK 설치에 실패해도 이미 복사한 Skill과 설치 없는 CLI는 사용할 수 있다. 설치에는 패키지 다운로드가 필요하다.

동일 Skill에 다시 실행하면 번들 파일을 갱신하고 추가 파일·기존 가상환경은 보존한다. 내용이 있는 다른 디렉터리를 임의로 덮어쓰거나, 설치 경로의 심볼릭 링크를 따라 다른 위치로 복사하지 않는다. 원본 저장소와 설치 Skill 폴더가 겹치는 경로는 거부한다.

자동 설치가 끝나면 **출력된 JSON을 제공 MCP 탭에 등록**하고 2~3번의 기본 확인, 5-3~5-4의 MCP 호출 확인을 진행한다. 기존 서버와 병합하는 방법·호스트별 JSON 형식은 5-2를 따른다. 스크립트는 과제 원본·Codex 설정 파일을 수정하거나 서버를 자동 등록하지 않는다. 실제 Cofa 연결 성공 여부는 호출 확인으로 판단한다.

### 0-1. 설치 후 MCP만 다시 점검

최신 설치 명령을 한 번 실행했다면 [점검 스크립트](skills/clarity-wiki/tools/check_mcp.py)가 Skill에 함께 들어 있다. 같은 과제 작업 폴더에서 아래 명령으로 언제든 재점검한다. 추가 패키지 다운로드 없이 설치된 가상환경의 Python을 사용한다.

```bash
.agents/skills/clarity-wiki/.venv/bin/python \
  .agents/skills/clarity-wiki/tools/check_mcp.py --root "$PWD"
```

단독 실행은 stdout에 점검 보고서 JSON을 출력한다. `status: passed`, `scope: local_stdio`, 종료 코드 `0`과 다음 네 항목의 `status: passed`가 성공 기준이다.

| 점검 항목 | 성공 기준 |
|---|---|
| `initialize` | 실제 서버 초기화 성공 |
| `tools/list` | `audit_revision`, `check_evidence` 두 도구 확인 |
| `audit_revision` | 합성 부호 변경에 `findings`·`NUMBER_CHANGED`·1개 이상 반환 |
| `check_evidence` | 합성 manifest·해시에 `no_findings`·0개 반환 |

SDK 누락·서버 시작 실패·도구 오류·예상과 다른 응답·시간 초과는 `status: failed`, 종료 코드 `2`로 보고한다. `stage`와 `error`에서 실패 위치와 이유를 확인한다. 기본 점검 제한은 30초이고 `--timeout 60`처럼 바꿀 수 있다. 시간 초과 시 서버 종료와 정리에 필요한 시간이 추가될 수 있다.

점검기는 작업 폴더에 고유한 `.clarity-mcp-check-*` 임시 디렉터리만 만들고 정상 종료·오류·시간 초과 시 정리한다. 합성 기록은 제출 근거로 사용하지 않는다. 이 결과는 독립 클라이언트의 로컬 stdio 연결 검증이다. Codex·Cofa에 등록한 연결은 5-4에서 별도로 확인한다. MCP 설정에 등록할 연결 JSON은 0번 설치 명령의 stdout을 사용한다.

## 1. 과제 작업 폴더에서 설치

웹 IDE 터미널에서 과제 작업 폴더에 있는지 확인한다. 아래 설치 명령은 현재 폴더를 바꾸지 않는다.

```bash
pwd
python3 --version
```

아래 블록을 복사해 실행한다. 공개 저장소를 임시 폴더에 Clone한 뒤 검증한 커밋 `5bc7864`의 Skill을 현재 프로젝트에 복사한다. 별도 pip 설치는 필요 없다. 같은 폴더에서 다시 실행하면 같은 Skill 파일을 덮어쓴다.

```bash
CW_SETUP_SRC="$(mktemp -d)" &&
git clone --quiet https://github.com/dailykim149656-source/clarity-wiki.git "$CW_SETUP_SRC" &&
git -C "$CW_SETUP_SRC" checkout --quiet --detach 5bc7864 &&
mkdir -p .agents/skills/clarity-wiki &&
cp -R "$CW_SETUP_SRC/skills/clarity-wiki/." .agents/skills/clarity-wiki/
```

프로젝트용 `.agents/skills` 경로와 `$skill-name` 호출은 [Codex 공식 Skill 문서](https://learn.chatgpt.com/docs/build-skills)에 안내되어 있다. 제공 환경의 실제 인식 여부는 다음 단계에서 확인한다.

## 2. CLI 정상 작동 확인

설치한 작업 폴더에서 구조 검사를 실행한다.

```bash
python3 .agents/skills/clarity-wiki/tools/validate.py
```

정상 출력과 종료 코드는 다음과 같다.

```text
PASS | Skill frontmatter and internal links | AppleDouble excluded | offline
```

종료 코드: `0`.

이어서 합성 예제의 근거 연결을 검사한다.

```bash
python3 .agents/skills/clarity-wiki/tools/clarity.py evidence \
  --root .agents/skills/clarity-wiki/examples/evidence \
  --manifest manifest.json
```

정상 결과는 출력 JSON의 `status`가 `no_findings`, `total_findings`가 `0`이며 종료 코드도 `0`인 것이다. 이는 예제의 파일·해시 구조 검사 성공이다. 합성 로그에 적힌 명령의 실제 실행이나 업무 정답을 인증하지 않는다.

## 3. 같은 작업 폴더에서 Codex 시작

웹 IDE 터미널에 준비된 Codex를 같은 작업 폴더에서 시작한다. 설치 전에 열린 세션에서 Skill이 보이지 않으면 세션을 다시 시작해 확인한다.

```bash
codex
```

다음은 **Codex 입력창에 붙여 넣는 사전 체험용 프롬프트**다. 터미널 셸 명령으로 실행하지 않는다.

```text
$clarity-wiki

지금은 사전 체험이다. 설치와 실행 확인만 진행해줘.

1. .agents/skills/clarity-wiki/SKILL.md를 실제로 읽고,
   적용한 파일 경로를 알려줘.
2. 시험 환경 프로필을 확인하고 다음 세 조건을 짧게 요약해줘:
   저장소 공개 유지 기간, Codex 업데이트 제한,
   제출 후 확인 문제에서의 AI 사용 제한.
3. .agents/skills/clarity-wiki/tools/clarity.py로
   .agents/skills/clarity-wiki/examples/evidence를 --root로 지정하고
   manifest.json을 실제 검사해줘.
   사용한 명령, 종료 코드, status와 total_findings를 보고해줘.

과제 파일이나 환경 설정은 변경하지 말고,
실행하지 못한 항목은 미확인으로 표시해줘.
```

| 확인 항목 | 성공 기준 |
|---|---|
| Skill 읽기 | 실제로 읽은 `SKILL.md` 경로를 제시 |
| 규정 반영 | 결과 통지 전까지 공개 유지·Codex 업데이트 금지·후속 확인 문제 AI 금지를 설명 |
| 도구 실행 | 실제 명령 실행 기록과 종료 코드 `0`, `no_findings`, `total_findings: 0`을 보고 |

모델의 성공 선언과 실제 명령 출력을 구분한다. 위 표가 충족되면 Skill 지침 읽기와 CLI 실행은 확인된 것이다. 제공 환경에서의 전체 과제 수행이나 MCP 연결까지 검증한 것은 아니다.

`$clarity-wiki`가 인식되지 않으면 Codex를 다시 시작한다. 계속 인식되지 않으면 프롬프트 첫 줄을 아래 문장으로 바꿔 파일을 직접 읽게 한다.

```text
.agents/skills/clarity-wiki/SKILL.md를 직접 읽고 지침을 적용해줘.
```

이 경우에는 자동 Skill 인식 성공으로 기록하지 않는다. 파일도 읽지 못하거나 CLI 실행이 막히면 원인을 미확인으로 남기고 허용된 수동 점검으로 전환한다. 제공 Codex를 업데이트하거나 설정 차단을 우회하지 않는다.

## 4. 선택: 수치 변경 감지 확인

시간이 남으면 Codex 입력창이 아닌 웹 IDE 터미널에서 실행한다. 임시 폴더에 합성 입력 두 개를 만든다.

```bash
CW_AUDIT_DIR="$(mktemp -d)"
printf '%s\n' '온도 -5°C' > "$CW_AUDIT_DIR/before.txt"
printf '%s\n' '온도 5°C' > "$CW_AUDIT_DIR/after.txt"

python3 .agents/skills/clarity-wiki/tools/clarity.py audit \
  --root "$CW_AUDIT_DIR" \
  --original before.txt \
  --revised after.txt
```

출력 JSON에 `status: findings`, `findings` 안에 `rule: NUMBER_CHANGED`가 있으면 정상적으로 변경을 감지한 것이다. **이 검사에서 종료 코드 `1`은 정상적인 경고 결과다.** 종료 코드 `2`는 잘못된 입력이며 검사 성공이 아니다.

## 5. 선택: 로컬 MCP 연결

1~3번의 Skill·CLI 확인을 마친 같은 작업 폴더에서 진행한다. 여기서는 복사한 Skill의 MCP 런처를 사용하며 **제공 Codex 버전은 그대로 유지**한다. MCP 설치에 필요한 패키지 다운로드와 실행 중의 로컬 stdio 통신은 구분한다. 검사 서버는 외부 LLM·API 키·HTTP 서버를 사용하지 않는다.

### 5-1. 전용 Python 환경에 SDK 설치

웹 IDE 터미널에서 실행한다. [공식 MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0) 버전은 패키지의 optional dependency와 같은 `1.30.0`으로 고정한다.

```bash
python3 -m venv .agents/skills/clarity-wiki/.venv &&
.agents/skills/clarity-wiki/.venv/bin/python -m pip install 'mcp==1.30.0' &&
.agents/skills/clarity-wiki/.venv/bin/python -c 'from importlib.metadata import version; print(version("mcp"))'
```

마지막 출력이 `1.30.0`이면 SDK 설치를 확인한 것이다. 아직 MCP 호스트 연결이나 도구 호출을 검증한 것은 아니다. 설치가 허용되지 않거나 실패하면 기존 CLI로 진행한다.

### 5-2. 실제 경로가 들어간 연결 JSON 생성

같은 작업 폴더에서 아래 명령을 실행한다. 설정 파일을 변경하지 않고 **현재 프로젝트의 절대 경로를 넣은 JSON을 출력**한다.

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd().resolve()
skill = root / ".agents/skills/clarity-wiki"
config = {"mcpServers": {"clarity-wiki": {
    "command": str(skill / ".venv/bin/python"),
    "args": [str(skill / "tools/mcp_server.py"), "--root", str(root)],
}}}
print(json.dumps(config, ensure_ascii=False, indent=2))
PY
```

출력 형식은 다음과 같다. 아래의 `/absolute/path/to/project`는 예시이며, **위 명령이 출력한 실제 경로의 JSON을 사용**한다.

```json
{
  "mcpServers": {
    "clarity-wiki": {
      "command": "/absolute/path/to/project/.agents/skills/clarity-wiki/.venv/bin/python",
      "args": [
        "/absolute/path/to/project/.agents/skills/clarity-wiki/tools/mcp_server.py",
        "--root",
        "/absolute/path/to/project"
      ]
    }
  }
}
```

제공된 MCP 탭에서 호스트 안내에 따라 등록·저장한다.

`mcpServers` 형식을 받는 경우 위 JSON을 사용한다. 서버 한 개의 객체를 요구하는 호스트에서는 `clarity-wiki` 안쪽의 `command`·`args` 객체를 사용한다. 기존 서버가 있다면 해당 설정을 보존하고 `clarity-wiki`를 추가한다. MCP 호스트에서도 같은 Python 실행 파일과 작업 폴더에 접근할 수 있어야 하며, 실제 Cofa 환경의 설정 형식과 시작 성공 여부는 사전 체험에서 확인한다.

`--root`는 검사할 과제 작업 폴더다. 위 설정은 이를 명시하므로 `CLARITY_WORKSPACE_ROOT` 환경변수나 `${PLUGIN_ROOT}` 치환이 필요 없다. 호스트가 서버를 시작하며, 일반 `python3` 대신 **SDK가 설치된 가상환경의 Python**을 지정해야 한다.

### 5-3. 도구 호출용 합성 입력 준비

검사 경로는 모두 서버의 `--root` 기준이다. 기존 예제 manifest를 그대로 프로젝트 root에서 호출하면 내부의 `input.csv` 등을 찾지 못할 수 있다. 아래 명령은 Skill 안의 `examples/mcp-check`에 합성 파일을 복사하고 manifest의 모든 파일 경로에 작업 폴더 기준 접두사를 붙인다. 과제 원본 파일은 변경하지 않는다.

```bash
python3 - <<'PY'
import json
import shutil
from pathlib import Path

skill = Path(".agents/skills/clarity-wiki")
source = skill / "examples/evidence"
probe = skill / "examples/mcp-check"
probe.mkdir(parents=True, exist_ok=True)
for name in ("input.csv", "result.csv", "verification.txt"):
    shutil.copyfile(source / name, probe / name)

document = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
def prefixed(name):
    return (probe / name).as_posix()
document["artifacts"] = [prefixed(name) for name in document["artifacts"]]
for requirement in document["requirements"]:
    for evidence in requirement["evidence"]:
        evidence["path"] = prefixed(evidence["path"])
        for item in evidence["inputs"]:
            item["path"] = prefixed(item["path"])
(probe / "manifest.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
(probe / "before.txt").write_text("온도 -5°C\n", encoding="utf-8")
(probe / "after.txt").write_text("온도 5°C\n", encoding="utf-8")
print("READY:", probe.as_posix())
PY
```

정상 출력은 `READY: .agents/skills/clarity-wiki/examples/mcp-check`다. 이 합성 기록은 실제 과제의 검증 근거로 제출하지 않는다.

### 5-4. Codex에서 실제 MCP 호출 확인

허용된 MCP 설정을 저장·연결하고, 필요하면 제공 Codex 세션을 다시 시작한다. 다음 프롬프트를 **Codex 입력창**에 붙여 넣는다.

```text
지금은 로컬 MCP 연결 확인이다.
연결된 clarity-wiki 서버의 도구 목록에서
audit_revision과 check_evidence 두 도구를 확인해줘.

이어서 다음 인자로 각각 한 번씩 실제 MCP 도구를 호출해줘.

audit_revision:
{"original":".agents/skills/clarity-wiki/examples/mcp-check/before.txt","revised":".agents/skills/clarity-wiki/examples/mcp-check/after.txt","limit":5}

check_evidence:
{"manifest":".agents/skills/clarity-wiki/examples/mcp-check/manifest.json","limit":5}

서버명, 실제 호출한 도구명, 결과의 status·total_findings와 오류 여부를 보고해줘.
CLI나 직접 Python 실행으로 대신하지 말고,
MCP 도구가 없거나 호출에 실패하면 연결 미확인으로 보고해줘.
과제 파일이나 환경 설정은 변경하지 마.
```

| 확인 항목 | 정상 기준 |
|---|---|
| 도구 목록 | `clarity-wiki` 서버에 `audit_revision`, `check_evidence` 두 도구가 있음 |
| 수치 변경 호출 | 오류 없이 `status: findings`, `total_findings` 1 이상, `rule: NUMBER_CHANGED` 반환 |
| 근거 검사 호출 | 오류 없이 `status: no_findings`, `total_findings: 0` 반환 |

MCP 응답이 `isError: true`이거나 실제 호출 기록이 없으면 성공으로 기록하지 않는다. MCP에서는 CLI 종료 코드 `1`을 성공 기준으로 쓰지 않고 응답의 오류 여부와 결과 필드를 확인한다. 서버가 시작됐다는 표시만으로 두 도구의 호출 성공을 대신하지 않는다.

| 증상 | 확인할 것 |
|---|---|
| `No module named mcp` 또는 SDK 없음 | JSON의 `command`가 위 가상환경 Python인지와 SDK 설치 결과 |
| 실행 파일·런처를 찾지 못함 | 생성한 절대 경로가 맞는지, MCP 호스트가 같은 파일 경로에 접근하는지 |
| 근거 파일 누락·해시 경고 | 합성 입력 준비를 완료했는지, `--root`가 현재 과제 작업 폴더인지 |
| MCP 도구가 안 보이거나 연결 실패 | 제공 설정의 저장·연결 상태 확인 후, 실패가 지속되면 CLI·수동 점검으로 전환 |

## 6. 본 응시 시작 프롬프트

본 응시에서 새 작업 폴더가 열리면 설치와 인식을 다시 확인한다. 사전 체험의 파일·세션이 유지된다고 가정하지 않는다. 본 과제가 시작된 뒤 아래 프롬프트를 제공 Codex에 입력한다.

```text
$clarity-wiki

README와 제공 자료, 기존 코드를 먼저 읽어줘.
필수 산출물과 제출 조건, 검증 가능한 완료 기준을 정리하고,
자료로 해결되지 않는 중요한 질문만 최대 3개로 추려줘.

답이 필요한 부분과 독립적으로 진행할 일을 구분하고,
구현 후 실제 테스트와 원자료 대조 근거를 작업 공간에 기록해줘.
미검증 항목은 완료로 표현하지 말고,
보고서에서는 수치·단위·조건·주장 강도를 보존해줘.
```

사전 체험은 1회·15분이다. MCP는 기본 확인 이후 시간이 남고 허용된 설정으로 연결할 수 있을 때 위 5번에 따라 점검하며, 일반적인 설정 설명은 [MCP 사용 안내](docs/USAGE.md#mcp-연결)를 참고한다. 시험에서 사용하는 저장소는 2차 예선 결과 통지 전까지 공개로 유지하고, 시험 파일·결과·작업 이력은 외부 업로드나 Git Push를 하지 않는다. 제출 후 AI 사용 금지 확인 문제에서는 AI 지원을 중단한다.
