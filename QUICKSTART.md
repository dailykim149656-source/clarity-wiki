# Clarity Wiki 사전 체험 빠른 시작

갱신일: 2026-10-30 (Asia/Seoul). 사전 체험에서 설치하고 정상 작동을 확인하는 순서다. **감독 앱·촬영 연결을 먼저 확인한 뒤 Skill과 CLI를 점검한다.** MCP는 시간이 남을 때 선택적으로 확인한다.

필요 환경은 Git, Python 3.10 이상, POSIX 파일 읽기를 지원하는 macOS/Linux다. 제공 Codex는 업데이트하지 않으며 개인 계정·API 키를 연결하지 않는다. 이 문서는 [시험 환경 프로필](skills/clarity-wiki/references/shared/exam-boundaries.md)의 운영 메일·기존 가이드 제한을 함께 따른다.

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

## 5. 본 응시 시작 프롬프트

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

사전 체험은 1회·15분이다. MCP는 기본 확인 이후 시간이 남고 허용된 설정으로 연결할 수 있을 때 [MCP 사용 안내](docs/USAGE.md#mcp-연결)에 따라 점검한다. 시험에서 사용하는 저장소는 2차 예선 결과 통지 전까지 공개로 유지하고, 시험 파일·결과·작업 이력은 외부 업로드나 Git Push를 하지 않는다. 제출 후 AI 사용 금지 확인 문제에서는 AI 지원을 중단한다.
