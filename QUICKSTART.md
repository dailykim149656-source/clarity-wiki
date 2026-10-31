# QUICKSTART: Skill과 CLI

Python 3.10 이상과 POSIX 파일 접근을 지원하는 macOS/Linux용이다. 추가 패키지를 설치하지 않고 Skill과 번들 CLI를 사용할 수 있다.

## 먼저 목적 선택

| 목적 | 시작 위치 |
|---|---|
| 실제 과제 시작 | [기본 Codex용 짧은 프롬프트](START_HERE.md#짧은-시작-프롬프트) |
| 시나리오 담당자에게 확인할 질문 준비 | [질문·답변 반영 프롬프트](skills/clarity-wiki/references/scenario-questions.md) |
| Skill과 CLI 설치 | 아래 1번 |
| 설치 상태와 검사 동작 확인 | 아래 2번 |
| 실제 과제 파일 검사 | [CLI 사용 안내](docs/USAGE.md) |

작업 시작에 설치·합성 예제 점검·새 기록 파일이 필수인 것은 아니다. 과제 자체의 실행·테스트·원자료 대조를 우선한다.

## 1. 과제 작업 폴더에서 설치

제공 터미널에서 현재 위치와 Python 버전을 확인한다. 다음 명령은 현재 작업 폴더를 바꾸지 않는다.

```bash
pwd
python3 --version
```

아래 블록은 공개 저장소의 현재 `main`을 임시 폴더로 받고, 현재 프로젝트에 Skill과 CLI를 복사한다. 실제 받은 커밋도 출력한다.

```bash
CW_SETUP_SRC="$(mktemp -d)" &&
git clone --depth 1 --quiet https://github.com/dailykim149656-source/clarity-wiki.git "$CW_SETUP_SRC" &&
python3 "$CW_SETUP_SRC/tools/install.py" --root "$PWD" &&
git -C "$CW_SETUP_SRC" rev-parse --short HEAD
```

이미 받은 저장소를 쓰면 `python3 /저장소의/절대경로/tools/install.py --root "$PWD"`로 실행한다. `--root` 생략 시 현재 폴더가 대상이다. 설치기는 공개 Skill 파일을 `.agents/skills/clarity-wiki`로 복사하고 구조와 CLI 버전을 검사한다. 성공은 종료 코드 `0`, 실패는 `2`다. 가상환경·SDK·연결 설정은 만들지 않는다. 진행·검사 결과는 stderr로 출력한다.

동일 Skill 재설치 시 번들 파일을 갱신하고 추가 파일은 보존한다. 다른 내용의 디렉터리와 경로 이탈을 유발하는 설치 경로는 거부한다. 기존 과제 파일·Codex 설정을 수정하지 않는다. 과거 버전의 추가 파일이나 호스트 등록까지 자동 삭제하는 설치기는 아니다.

## 2. 정상 작동 확인

설치한 과제 작업 폴더에서 다음을 실행한다.

```bash
python3 .agents/skills/clarity-wiki/tools/validate.py
python3 .agents/skills/clarity-wiki/tools/clarity.py --version
python3 .agents/skills/clarity-wiki/tools/clarity.py evidence \
  --root .agents/skills/clarity-wiki/examples/evidence \
  --manifest manifest.json
```

| 확인 | 정상 결과 |
|---|---|
| 구조 검사 | `PASS ...`와 종료 코드 `0` |
| CLI 버전 | `0.4.0`과 종료 코드 `0` |
| 합성 manifest 검사 | JSON의 `status: no_findings`, `total_findings: 0`, 종료 코드 `0` |

합성 manifest는 서식 예시다. 통과는 파일·선언된 해시 구조 확인이며 실제 과제의 테스트 실행이나 정답을 인증하지 않는다.

Skill을 사용할 상황이면 Codex 입력창에서 다음과 같이 호출한다. 셸 명령이 아니다.

```text
$clarity-wiki 현재 과제에서 결과를 바꾸는 미확정 조건만 골라 질문 초안을 만들어줘.
```

자동 인식이 되지 않으면 `.agents/skills/clarity-wiki/SKILL.md`의 실제 경로를 Codex에 알려 직접 읽게 한다. 계속 사용할 수 없으면 실제 지시서와 기본 Codex로 작업을 진행한다.

## 3. 시나리오 에이전트에게 질문

[시나리오 질문 안내](skills/clarity-wiki/references/scenario-questions.md)에는 다음 세 문구가 있다.

1. Codex에 지시서·제공 자료를 읽히고 중요한 미확정 질문을 준비하는 프롬프트.
2. 참가자가 허용된 메신저에 직접 보내는 질문 문구.
3. 실제 답변을 Codex에 전달해 확정 범위·처리 규칙·검증 기준을 갱신하는 프롬프트.

한 번에 중요한 질문 최대 3개를 다루며, 새로 중요한 불확실성이 생기면 추가 확인한다. 답이 없는 부분을 확정하지 않고 독립적인 작업을 계속한다.

## 4. 수치·인용 변경 검사

과제 폴더 안에 실제 비교할 `before.md`, `after.md`가 있을 때 실행한다.

```bash
python3 .agents/skills/clarity-wiki/tools/clarity.py audit \
  --root "$PWD" --original before.md --revised after.md --limit 5
```

발견 항목이 있으면 JSON과 종료 코드 `1`이 정상적인 검토 요청이다. 잘못된 경로나 입력은 `2`다. 전체 의미와 업무 정답은 원자료와 직접 대조한다. 근거 manifest가 실제로 필요한 경우에만 [형식 안내](skills/clarity-wiki/references/local-checks.md)를 사용한다.

## 5. 제한된 환경의 점검 순서

최신 공식 안내에 따라 응시자가 감독 환경을 먼저 확인한다. 이어 실제 지시서 읽기 → 연습 결과 저장·재열기 → 과제 실행·원자료 대조를 확인하고, 남은 시간에 필요한 Skill·CLI만 점검한다. 선택 설치가 실패하면 반복 설치 대신 기본 Codex·기존 터미널 검사·수동 대조로 진행하고 미수행 범위를 남긴다.

기존 회차의 날짜·체험 시간·허용 조건을 재응시에 그대로 적용하지 않는다. [시험 환경 프로필](skills/clarity-wiki/references/shared/exam-boundaries.md)의 원회차 출처와 새 안내를 구분한다. AI 금지 단계에서는 지원을 중단하며 실제 시험 자료·결과·작업 이력은 외부 전송·Git Push하지 않는다.
