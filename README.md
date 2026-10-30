# Clarity Wiki 0.3.0

요구사항, 결정, 검증 근거를 연결하는 한국어 Codex Skill과 로컬 검사 도구입니다.

`자료 확인 → 중요한 질문 → 완료 조건 → 구현·검증 → 근거 있는 보고`를 돕습니다. 파일 검사기는 외부 모델·API 키·네트워크 없이 실행됩니다. Codex 모델 자체의 통신은 별개입니다.

## 바로 사용

**과제를 시작하려면 [START_HERE](START_HERE.md)의 프롬프트 하나를 제공 Codex에 입력하세요.** 실제 과제 지시서와 Clarity Wiki 참고자료 경로를 구분하고, 필수 결과·중요한 질문·실행·검증으로 이어갑니다. 시작 프롬프트는 그 문서에서 관리합니다.

설치·사전 체험·도구 점검이 필요하면 [QUICKSTART의 목적별 안내](QUICKSTART.md#먼저-목적-선택)를 고르세요. 기본 과제 진행에 CLI·MCP 설치나 새 기록 파일 작성이 필수인 것은 아닙니다.

Skill과 로컬 MCP를 함께 설치하려면 과제 작업 폴더에서 `python3 /저장소의/절대경로/tools/install.py --root "$PWD" --check`를 실행합니다. [설치 스크립트](tools/install.py)가 전용 가상환경에 SDK를 설치하고, `--check`로 두 도구를 실제 호출한 뒤 절대 경로의 연결 JSON을 출력합니다. 공개 저장소를 가져오는 명령부터는 [한 번에 설치](QUICKSTART.md#0-skillmcp-한-번에-설치)를 참고하세요. JSON 등록은 제공 MCP 호스트에서 진행합니다.

설치 후 재점검은 `.agents/skills/clarity-wiki/.venv/bin/python .agents/skills/clarity-wiki/tools/check_mcp.py --root "$PWD"`로 실행합니다. [점검 스크립트](skills/clarity-wiki/tools/check_mcp.py)는 합성 파일을 만들고 정리하며, 실제 MCP 초기화·두 도구 호출 결과를 JSON으로 보고합니다. 성공은 종료 코드 `0`, 실패는 `2`입니다. Codex·Cofa의 설정 등록 상태는 별도로 확인해야 합니다.

참고자료를 아직 받지 않았다면 허용된 과제 작업 폴더에서 아래 명령으로 받습니다. 받은 뒤 과제 작업 폴더를 유지하며 시작 안내를 사용합니다.

```bash
git clone https://github.com/dailykim149656-source/clarity-wiki.git
```

아래 CLI 예시는 이 저장소 루트 기준입니다. 과제 폴더에서는 런처를 실제 절대 경로로 지정합니다. Python 3.10 이상과 POSIX 파일 읽기를 지원하는 macOS/Linux에서 설치 없이 CLI를 실행할 수 있습니다. 작업 파일 경로는 `--root`를 기준으로 해석합니다. Windows의 직접 실행은 현재 지원하지 않습니다.

```bash
python3 skills/clarity-wiki/tools/validate.py
python3 skills/clarity-wiki/tools/clarity.py audit --root ./workspace --original old.txt --revised new.txt
python3 skills/clarity-wiki/tools/clarity.py evidence --root ./workspace --manifest manifest.json
```

종료 코드는 `0`: 검사 범위에서 발견 없음, `1`: 검토할 항목 있음, `2`: 잘못된 입력입니다. 검사는 JSON을 반환합니다. `no_findings`는 의미 보존·업무 정답·테스트 실행의 증명이 아닙니다.

## Skill 설치

사용할 프로젝트에서 이 저장소의 `skills/clarity-wiki` 폴더를 `.agents/skills/clarity-wiki`로 복사합니다. 개인 기본 문체나 비공개 자료를 포함하지 않습니다.

```bash
mkdir -p .agents/skills
cp -R /absolute/path/to/clarity-wiki/skills/clarity-wiki .agents/skills/
```

설치한 Skill은 Codex에서 `$clarity-wiki`로 호출할 수 있습니다. 실제 과제를 시작할 때는 [시작 프롬프트](START_HERE.md#제공-codex에-넣을-시작-프롬프트)를 사용합니다. Skill 디렉터리 안에 검사 코드도 포함되어 있어 저장소 전체나 pip 설치가 필요하지 않습니다. 현재 풀린 원본 v0.1은 `skills/clarity-wiki/`로 통합했고, v0.2의 간결한 로딩 방식을 반영했습니다.

## 두 검사 도구

| 도구 | 확인하는 것 | 한계 |
|---|---|---|
| `audit_revision` | 수치·부호·단위·직접 인용·짧은 대상 문맥의 변경 후보와 위치 | 의미·인과·전체 사실의 정확성은 판단하지 않음 |
| `check_evidence` | 증거 구조: manifest 형식, 필수 파일, 빈 파일, 선언된 증거·입력의 SHA-256 일치, 미검증 상태 | 명령 실행을 인증하지 않음. `artifacts`에만 적힌 파일의 내용 변경은 해시 연결이 필요 |

두 도구 모두 읽기 전용이며 셸 명령을 실행하지 않습니다. 경로는 명시한 작업 폴더 안으로 제한하고, 심볼릭 링크의 폴더 밖 접근과 과대 파일을 거부합니다. 입력 텍스트는 최대 256 KiB, 증거 파일은 각각 최대 8 MiB, evidence 한 번의 고유 파일은 최대 256개·합계 64 MiB입니다. 응답 경고는 기본 5개, 최대 30개입니다. 해시가 같은 것은 제공된 manifest와 일치한다는 뜻입니다. 검사 전후 파일 변경까지 봉쇄하는 OS 샌드박스는 아닙니다.

## 선택적 MCP·Plugin

CLI core는 표준 라이브러리만 사용합니다. MCP를 쓰려면 시작할 Python 환경에 공식 SDK가 필요합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[mcp]'
.venv/bin/clarity-wiki-mcp --root /absolute/path/to/workspace
```

`plugin.json`, `mcp.json`, `skills/`를 같은 루트로 묶었습니다. Plugin의 `python3`에도 MCP extra가 설치돼 있어야 하며, 시작 환경에 **절대 경로인 `CLARITY_WORKSPACE_ROOT`**를 지정해야 합니다. 지정하지 않으면 서버는 시작을 거부합니다. 호스트가 이 환경변수를 전달하지 않으면 [사용 안내](docs/USAGE.md)의 명시적 `--root` MCP 설정을 사용하세요. MCP 시작을 위해 감독·관리 설정을 변경하거나 차단을 우회하지 않습니다.

공식 Plugin Directory 등록·승인이나 Cofa 환경 설치를 완료한 패키지는 아닙니다. Plugin 호스트의 manifest 지원과 제공 환경의 적용 방법을 확인해야 합니다. MCP가 불가능하면 같은 CLI 또는 Skill 수동 점검을 사용합니다.

## 검증·배포

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

MCP SDK가 없는 환경에서는 transport 테스트가 생략됩니다. extra 설치 후 같은 명령을 실행하면 실제 SDK client/server stdio 왕복까지 검사합니다. [검증 범위](docs/VERIFICATION.md)에 실행 결과와 한계를 기록합니다. 릴리스 ZIP은 명시한 공개 소스만 담고 SHA-256 파일을 생성합니다. 원본 ZIP·규정 PDF·개인 프로필·조사 기록·캐시는 제외합니다.

대회 조건은 2026-10-30 제공 운영 메일을 반영한 [환경 프로필](skills/clarity-wiki/references/shared/exam-boundaries.md)에 분리했습니다. **사용하는 저장소는 2차 예선 결과 통지 전까지 공개로 유지**하고, **제공 Codex는 업데이트하지 않습니다**. 공개 자료는 기존 가이드의 허용 범위에서 활용하며 외부 자료로 결과물 전체를 대체할 수 없습니다. 실제 호스트 설치·실행은 사전 체험에서 확인합니다. [체험 순서](docs/USAGE.md#대회-사전-체험과-운영)대로 Skill·CLI부터 확인하고, 후속 서술형에서는 AI 기능을 사용하지 않습니다.

새로 작성한 코드·문서는 MIT 라이선스입니다. 방법론 출처와 재배포 경계는 [SOURCES](skills/clarity-wiki/SOURCES.md)를 참고하세요.
