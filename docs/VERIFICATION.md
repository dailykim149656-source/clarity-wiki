# 검증 범위

실행일: 2026-10-26 (사용자 시간대 기준). Python 3.12의 격리 환경과 공식 MCP SDK 1.30.0에서 전체 59개 테스트가 통과했습니다. SDK 없는 Python 3.14에서도 검사 core·CLI·패키징은 통과하며 실제 transport 한 개는 의도적으로 skip됩니다.

| 검증 | 결과 |
|---|---|
| 부호·단위·대상별 값·인용의 회귀 사례 | 통과 |
| manifest schema·누락·빈 파일·오래된 해시·읽기 예산 | 통과 |
| 실제 CLI 종료 코드·오류 JSON·다른 cwd·복사 설치 | 통과 |
| 경로 이탈·외부 심볼릭 링크·검사 중 디렉터리 교체 | 통과 |
| 잘못된 Unicode·과대 입력·비정규 파일 | 통과 |
| AppleDouble 제외·재현 가능한 릴리스 ZIP | 통과 |
| 공식 SDK client/server stdio initialize·두 도구 호출·오류·종료 | 통과 |
| portable plugin.json·mcp.json 공식 JSON Schema | 통과 |
| 소스 폴더와 깨끗한 압축 해제본의 pip 설치 | 통과 |

독립 리뷰에서 발견한 중간 디렉터리 교체에 의한 경로 이탈과 surrogate 입력 문제는 실패 재현 후 수정했습니다. 파일 읽기는 root 디렉터리 descriptor에 고정하고 각 경로 구성 요소에 no-follow를 적용합니다. 이 구현은 POSIX dir_fd/O_NOFOLLOW를 지원하는 macOS/Linux를 대상으로 합니다.

외장 디스크에서 setuptools 빌드가 AppleDouble 메타데이터 처리 중 실패한 것을 재현했습니다. 최종 빌드는 Hatchling의 명시적 패키지 경로를 사용하며 같은 소스 위치에서 설치를 다시 확인했습니다. 이는 빌드 시 의존성이고 기본 CLI 실행 시 의존성은 없습니다.

검증 대상은 숫자·부호·단위·인용 변경 후보, 근거 manifest 구조와 해시, 작업 경로 경계, CLI 종료 코드, 복사한 Skill 실행, AppleDouble 제외, 재현 가능한 ZIP, 실제 MCP stdio 연결입니다.

```bash
python3 skills/clarity-wiki/tools/validate.py
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

MCP transport 검증은 `.[mcp]` extra를 설치한 Python에서 위 테스트 명령을 실행해야 합니다. SDK 없는 기본 Python에서는 해당 테스트가 skip되므로 MCP가 검증됐다고 해석하지 않습니다.

초기 RED는 알려진 구조 검사 실패와 부호·단위·값 뒤바뀜 누락, 아직 없는 모듈·런처·패키징 기능에서 확인했습니다. GREEN은 실제 파일·서브프로세스·transport 검증으로 확인합니다. 로그·조사 기록은 공개 패키지에 포함하지 않습니다.

모의 과제의 정답·실제 대회 환경 설치·Skill을 쓴 모델의 행동 품질·시간 및 토큰 절감 효과는 이 자동 테스트로 검증하지 않았습니다. 기본 Codex/Skill/Skill+CLI 비교는 같은 모델·문제·시간 한도와 실행 순서·학습 효과를 통제해 별도로 기록해야 합니다. 파일 바이트 감소를 토큰 절감률로 바꾸지 않습니다.

Plugin manifest와 런처는 소스 패키지 수준의 검증 대상입니다. 특정 Plugin 호스트의 설치 완료나 공식 디렉터리 승인까지 의미하지 않습니다.

## 2026-10-30 통합 설치 스크립트 추가 검증

Python 3.12와 공식 MCP SDK 1.30.0 환경에서 설치 스크립트 회귀 테스트 13개를 포함한 전체 72개 테스트가 통과했습니다. 기존 디렉터리 보존, 원본·설치 경로 겹침, SDK 설치 실패 시 성공 JSON 미출력, 외부 파일로 향하는 가상환경 설정 링크 거부를 확인했습니다.

Python 3.14에서는 공백·한글이 있는 작업 폴더 안에 원본 저장소를 둔 상태로 새 가상환경·SDK를 실제 설치했습니다. 재실행 시 추가 파일·기존 가상환경·과제 파일·Codex 설정 보존과 Python 3.14의 추가 실행 파일 링크 처리를 확인했습니다. stdout의 연결 JSON으로 서버를 시작해 stdio 초기화, 정확히 두 도구의 목록, `audit_revision`·`check_evidence`의 실제 호출도 통과했습니다. 실제 Cofa 호스트의 설정 등록·Skill 인식은 사전 체험에서 별도로 확인해야 합니다.
