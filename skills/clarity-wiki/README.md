# Clarity Wiki v0.3.0

모호한 요구사항을 완료 조건과 검증 근거에 연결하는 Codex Skill입니다. 한국어 기술 문서 윤문은 원문의 사실과 주장 강도를 보존합니다.

## Skill만 사용

이 폴더 전체를 사용하는 호스트의 Skill 디렉터리에 복사합니다. `SKILL.md`와 `references/`가 기본 경로이며, 번들 CLI를 쓰려면 `tools/`와 `scripts/`도 함께 보존합니다. 호스트마다 Skill 발견·설정 방식이 다르므로 실제 인식을 확인합니다.

`$clarity-wiki README를 읽고 중요한 질문 최대 3개와 검증 가능한 완료 조건을 정리해줘.`

기본은 `clarify → contract → verify → report`입니다. 참고 문서는 주 문서 1개와 조건부 1개만 읽습니다. [작업 기록 양식](examples/work-record.md)을 상황에 맞게 사용하고, 실제 산출물 이름은 과제나 프로젝트 요구를 따릅니다.

## 로컬 CLI

Python 3.10 이상이 필요합니다. 직접 실행은 패키지 설치가 필요 없습니다. 아래 `<SKILL_DIR>`는 이 폴더의 절대 경로, `<WORKSPACE>`는 검사할 프로젝트의 절대 경로로 바꿉니다. 입력 경로는 작업 공간 기준입니다.

```sh
python3 '<SKILL_DIR>/tools/clarity.py' audit --root '<WORKSPACE>' --original old.txt --revised new.txt --limit 5
python3 '<SKILL_DIR>/tools/clarity.py' evidence --root '<WORKSPACE>' --manifest manifest.json --limit 5
python3 '<SKILL_DIR>/tools/validate.py'
```

저장소에서 선택적으로 패키지를 설치한 경우 `clarity-wiki audit`와 `clarity-wiki evidence`에 동일한 인자를 전달할 수 있습니다. 복사한 Skill만으로 이 설치형 명령이 생기지는 않습니다. 입력·결과·종료 코드와 합성 예제는 [로컬 검사](references/local-checks.md)를 참고합니다.

선택적 stdio MCP는 같은 core의 `audit_revision`, `check_evidence` 두 도구만 제공합니다. MCP SDK와 호스트 설정은 별도이며, 연결할 수 없으면 위 CLI를 사용합니다. CLI도 사용할 수 없다면 원자료를 수동 대조하고 자동 검사 미수행을 기록합니다.

## 범위

CLI와 MCP는 명시한 작업 공간 안의 파일만 읽으며 원본 파일을 수정하지 않습니다. 심볼릭 링크를 통한 경계 밖 접근과 과도한 입력을 거부하고 출력 건수를 제한합니다. 외부 LLM 호출, API 키, 네트워크 전송, 텔레메트리, 임의 셸 실행 기능은 없습니다. 사용자의 Codex 서비스 통신까지 차단하는 기능은 아닙니다.

`no_findings`는 정해진 규칙에서 경고를 찾지 못했다는 뜻입니다. 의미 보존, 업무 정답, 로그의 실제 실행 여부, 사람 검토를 증명하지 않습니다. `validate.py`는 패키지 구조 검사이며 실제 호스트에서의 Skill 선택이나 시험 환경 승인을 보장하지 않습니다.

## 선택 자료

- [호출과 윤문 예시](examples/requests.md)
- [일반 기술 문체 프로필](profiles/generic-technical.md): 명시적으로 선택할 때만 적용
- [시험 경계](references/shared/exam-boundaries.md): 해당 환경에서만 적용하는 2026-10-30 갱신 요약
- [출처](SOURCES.md)

공개 패키지에는 개인 프로필, 실제 과제·시험 데이터, 규정 PDF, 개인 작업 로그를 넣지 않습니다. 시험에서 사용하는 저장소는 2차 예선 결과 통지 전까지 공개로 유지하며, 제공 Codex 버전을 업데이트하지 않습니다. 운영 메일과 기존 가이드가 충돌하면 메일이 우선입니다. 메시지·화면·제출은 응시자가 직접 처리하고, AI 금지 후속 서술형에서는 사용을 중단합니다.
