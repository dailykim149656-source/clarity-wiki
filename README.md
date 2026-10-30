# Clarity Wiki 0.3.0

요구사항, 결정, 검증 근거를 연결하는 한국어 Codex Skill과 로컬 검사 도구입니다.

`자료 확인 → 중요한 질문 → 완료 조건 → 구현·검증 → 근거 있는 보고`를 돕습니다. 파일 검사기는 외부 모델·API 키·네트워크 없이 실행됩니다. Codex 모델 자체의 통신은 별개입니다.

## 바로 사용

공개 저장소를 내려받고 저장소 폴더에서 실행합니다.

```bash
git clone https://github.com/dailykim149656-source/clarity-wiki.git
cd clarity-wiki
```

Python 3.10 이상과 POSIX 파일 읽기를 지원하는 macOS/Linux에서 설치 없이 CLI를 실행할 수 있습니다. 작업 파일 경로는 `--root`를 기준으로 해석합니다. Windows의 직접 실행은 현재 지원하지 않습니다.

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

Codex에서 `$clarity-wiki README를 읽고 중요한 모호성과 완료 조건을 정리해줘`처럼 호출합니다. Skill 디렉터리 안에 검사 코드도 포함되어 있어 저장소 전체나 pip 설치가 필요하지 않습니다. 현재 풀린 원본 v0.1은 `skills/clarity-wiki/`로 통합했고, v0.2의 간결한 로딩 방식을 반영했습니다.

## 두 검사 도구

| 도구 | 확인하는 것 | 한계 |
|---|---|---|
| `audit_revision` | 수치·부호·단위·직접 인용·짧은 대상 문맥의 변경 후보와 위치 | 의미·인과·전체 사실의 정확성은 판단하지 않음 |
| `check_evidence` | manifest 형식, 필수 파일, 빈 파일, 증거·입력의 SHA-256 일치, 미검증 상태 | 제공된 명령·상태·로그의 실제 실행을 인증하지 않음 |

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
