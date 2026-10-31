# CLI 사용 안내

과제 시작은 [START_HERE](../START_HERE.md), 설치·점검은 [QUICKSTART](../QUICKSTART.md), 시나리오 담당자 질문은 [질문 프롬프트](../skills/clarity-wiki/references/scenario-questions.md)를 사용합니다.

## 설치 없이 실행

받은 저장소 또는 복사한 Skill의 `tools/clarity.py`를 Python으로 실행합니다. 아래 `<SKILL_DIR>`와 `<WORKSPACE>`는 실제 절대 경로로 바꿉니다. Python 3.10 이상, macOS/Linux의 POSIX 파일 접근이 필요합니다.

```bash
python3 '<SKILL_DIR>/tools/clarity.py' audit --root '<WORKSPACE>' --original before.md --revised after.md --limit 5
python3 '<SKILL_DIR>/tools/clarity.py' evidence --root '<WORKSPACE>' --manifest reports/manifest.json --limit 5
```

입력 경로는 현재 터미널 위치나 manifest 부모가 아닌 `--root` 기준입니다. 예를 들어 `/work/project/reports/manifest.json`의 `src/main.py`는 `/work/project/src/main.py`입니다. 작업 폴더 밖 입력과 경로 이탈은 거부합니다.

원문과 수정문은 UTF-8 텍스트입니다. 출력 위치는 1부터 시작하는 Unicode 문자 기준 행·열이며 바이트 위치가 아닙니다. 보고서에 새로 계산한 수치는 원자료·계산 결과로 검증하고, 윤문 전후 사실 보존 검사와 구분합니다.

선택적으로 패키지를 pip 설치한 환경에서는 `clarity-wiki audit`와 `clarity-wiki evidence`로 같은 인자를 전달할 수 있습니다. 복사한 Skill만으로 이 설치형 명령이 생기지는 않습니다. 직접 Python 실행에는 pip 설치가 필요하지 않습니다.

## 결과와 종료 코드

| 종료 코드 | 의미 |
|---|---|
| `0` | 해당 검사 범위에서 발견 없음 |
| `1` | 검토할 항목 있음 |
| `2` | 경로·형식 등 잘못된 입력 |

stdout은 JSON입니다. `total_findings`는 전체 후보 수, `findings`는 표시한 후보와 위치, `truncated`는 표시 잘림 여부, `limitations`는 판단하지 않는 범위입니다. `--limit`는 1–30입니다.

`audit`는 수치·부호·단위·인용·짧은 대상 문맥의 변경 후보를 찾습니다. 긴 대상명, 재정렬, 대상과 값이 다른 줄에 있는 경우는 놓칠 수 있습니다. 키별 값·조건·의미를 직접 대조합니다.

`evidence`는 manifest 구조·파일·선언된 해시를 검사합니다. `command`는 기록 문자열이며 검사기가 실행하지 않습니다. `artifacts`에 경로만 적은 파일은 존재·비어 있음만 확인하므로 내용 변경을 찾으려면 실제 검증 시점에 읽은 산출물도 해시에 연결해야 합니다. 형식과 예시는 [로컬 검사](../skills/clarity-wiki/references/local-checks.md)를 참고합니다.

## 실제 검증과 연결

과제 자체의 실행·테스트 또는 수동 원자료 대조를 수행한 뒤, 입력·코드 버전, 기대 동작, 실제 관측, 명령·종료 코드, 근거 위치를 연결합니다. 실행 실패·미실행·환경 차단을 구분하고 수행하지 않은 명령 결과나 사람 확인을 만들어 넣지 않습니다. 관련 코드나 입력을 수정했다면 해당 검증을 다시 실행합니다.

이 CLI의 `no_findings`는 실제 명령 실행, 업무 정답, 사람 검토 또는 성능 개선의 증명이 아닙니다. CLI를 사용할 수 없으면 가능한 수동 검토를 진행하고 자동 검사 미수행을 남깁니다.

제한된 환경에서는 [버전별 환경 프로필](../skills/clarity-wiki/references/shared/exam-boundaries.md)과 최신 공식 안내를 따릅니다. AI 금지 단계에서는 지원을 중단합니다. 실제 시험 파일·결과·작업 이력은 외부 전송·Git Push하지 않습니다.
