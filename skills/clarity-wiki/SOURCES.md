# 방법론 출처 및 권리 경계

이 패키지는 아래 프로젝트의 **아이디어와 검수 관점**을 참고해 독립적으로 작성한 문서형 Skill이다. 원본 SKILL.md, 소스코드, 데이터셋, 평가 룰북 전문, CLI, 실행 스크립트는 포함하지 않는다.

| 프로젝트 | 원천 내용 | 통합 Skill에 반영한 방법론 |
|---|---|---|
| [말매치 Malmatch](https://github.com/dailykim149656-source/malmatch) | 한국어 캐릭터 대사 검수 로컬 MCP | 자연스러움, 관계 적합성, 어체와 매체 적합성의 관점. 이 저장소의 MCP는 설치/실행하지 않는다. |
| [NomaDamas/k-skill, korean-humanizer](https://github.com/NomaDamas/k-skill/tree/main/korean-humanizer) | 번역투 및 관용구 검수 | 원문 의미 보존, 문제 구간만 수정하는 방식. `npx` CLI는 실행하지 않는다. |
| [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) | 한국어 문체 패턴 진단/윤문 | 의미 불변, 경향 진단, 과도한 재작성 방지. CLI를 복사하거나 실행하지 않는다. |
| [sumilee-phd/imnotai](https://github.com/sumilee-phd/imnotai) | 웹 기반 분석 및 윤문 서비스 | 다단계 분석/감사라는 검토 관점. 웹 API, Claude/Gemini/Solar 백엔드는 전혀 연결하지 않는다. 원 프로젝트 자체도 epoko77-ai/im-not-ai를 출처로 밝힌다. |
| [Q00/ouroboros](https://github.com/Q00/ouroboros) | 명세 우선, 소크라테스식 인터뷰와 모호성 관리 | 가정 원장, 중요한 질문 우선, 종료 기준. 원본 Agent OS/MCP 및 자동화 엔진은 사용하지 않는다. |
| [obra/superpowers](https://github.com/obra/superpowers) | brainstorming, 계획/테스트 절차 | 질문 전 자료 확인, 설계 대안 비교, 구현과 검증의 연결. 강제 승인/다단계 워크플로를 전부 복제하지 않는다. |

참고 프로젝트 중 일부는 MIT 라이선스를 표기한다. 다만 `malmatch` 최상위에는 확인 시점에 명시적 LICENSE 파일이 없었다. 따라서 포함된 문서와 코드를 별도 허가 없이 재배포하지 않는다. **이 패키지는 외부 프로젝트의 저작물을 번들링하지 않는다.**

직접 참고한 공식 형식: [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills), [Skill creator 가이드](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md).

출처 확인: 2026-10-26. 공개 저장소는 업데이트될 수 있으므로 장기 유지 보수 시 변경사항을 재검토한다.
