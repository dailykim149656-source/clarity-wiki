---
name: clarity-wiki
description: 모호한 요구사항을 명확히 하거나 수용 기준·완료 조건을 정할 때, 검증 근거를 정리하거나 한국어 기술 문서를 사실 보존하며 윤문할 때 사용한다.
---

# Clarity Wiki

요구사항, 결정, 검증 근거를 연결한다. 사용자 지시와 원자료를 우선하며, 이미 허용된 작업을 작은 승인 단계로 나누지 않는다.

## 진입점

기본 주 문서는 [작업 흐름](references/workflow.md)이다. **한 작업 단계에서 주 문서 1개와 필요한 조건부 문서 최대 1개만** 읽는다. 다음 단계에서 필요가 바뀌면 문서를 교체한다. 참고 문서 안의 링크도 추가로 전부 읽으라는 뜻이 아니다.

`clarify → contract → verify → report`

- **clarify**: 실제 과제 지시서와 참고 Skill 경로를 구분하고, 지시서·제공 자료·기존 코드를 먼저 읽는다. 결과를 바꾸는 질문만 최대 3개로 추린다. 미확인 조건의 영향과 확인 주체를 남기고 독립적으로 진행할 일을 나눈다.
- **contract**: 요구사항 ID, 원문 위치, 완료 기준, 검증 방법, 상태를 연결한다.
- **verify**: 실제 입력으로 확인하고 명령·결과·수행자를 연결한다. 기록이 필요한 작업은 과제가 요구한 설명이나 기존 기록에 근거를 남긴다. 실행하지 않은 검증은 미검증이다.
- **report**: 결과, 판단 근거, 수행한 검증, 남은 한계를 짧게 정리한다.

| 조건 | 선택할 문서 |
|---|---|
| 증거 manifest 또는 CLI 사용 | 조건부 [로컬 검사](references/local-checks.md) |
| 제한된 시험 환경이 명시됨 | 조건부 [버전별 시험 경계](references/shared/exam-boundaries.md) 우선 |
| 기술 문서 윤문만 요청 | 주 문서를 [technical](references/rewrite/technical.md)로 교체 |
| 짧은 글 / 대사 / 사실 변형 검수만 요청 | 각각 [quick](references/rewrite/quick.md), [dialogue](references/rewrite/dialogue.md), [fidelity](references/rewrite/fidelity.md) 중 하나로 교체 |
| 심층 탐색 / 반례 검토를 명시적으로 요청 | [deep](references/plan/deep.md) 또는 [stress](references/plan/stress.md)로 교체 |

## 보존과 한계

- 윤문에서는 수치, 단위, 인용, 조건, 주체, 주장 강도를 보존한다. 미확인 주장도 요청 없이 삭제·약화하지 않고 **별도 검토 의견**으로 표시한다.
- 검사 결과가 `no_findings`여도 의미·업무 정답·실제 테스트 실행·사람 검토를 입증하지 않는다.
- 번들 CLI는 작업 공간 안의 파일을 읽어 검사한다. 네트워크·외부 LLM·API 키·임의 명령 실행이 필요하지 않다. Codex 자체의 통신까지 오프라인이라는 뜻은 아니다.
- MCP는 선택 사항이다. 연결 실패 시 같은 CLI, CLI 사용 불가 시 수동 대조로 진행하고 자동 검사 미수행을 표시한다.

[호출 예시](examples/requests.md)와 [작업 기록 양식](examples/work-record.md)은 필요할 때만 사용한다. 출처는 [SOURCES.md](SOURCES.md)에 있다.
