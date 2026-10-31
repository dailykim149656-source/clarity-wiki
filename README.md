# Clarity Wiki 0.4.0

요구사항, 결정, 검증 근거를 연결하는 한국어 Codex Skill과 로컬 CLI입니다.

**기본 Codex로 실제 과제부터 읽고 진행합니다.** 질문이나 검증이 막힐 때 관련 Skill 문서를 선택하고, 필요한 파일 검사에 CLI를 사용합니다. 시작에 설치나 별도 기록 파일 작성이 필요한 것은 아닙니다.

## 바로 사용

| 목적 | 안내 |
|---|---|
| 기본 Codex로 과제 시작 | [짧은 시작 프롬프트](START_HERE.md) |
| 시나리오 담당자에게 중요한 조건 확인 | [질문 준비·전달·답변 반영 프롬프트](skills/clarity-wiki/references/scenario-questions.md) |
| Skill과 번들 CLI 설치·점검 | [QUICKSTART](QUICKSTART.md) |
| 수치·인용 변경 또는 근거 파일 검사 | [CLI 사용 안내](docs/USAGE.md) |

공개 저장소를 받은 뒤 과제 작업 폴더에서 설치합니다. 대상 폴더가 이미 있으면 기존 저장소를 사용합니다.

```bash
git clone https://github.com/dailykim149656-source/clarity-wiki.git
python3 clarity-wiki/tools/install.py --root "$PWD"
```

설치기는 `.agents/skills/clarity-wiki`에 Skill과 CLI를 복사하고 구조와 CLI 버전을 검사합니다. Python 3.10 이상과 POSIX 파일 접근을 지원하는 macOS/Linux에서 동작하며 실행에 추가 패키지·API 키·외부 모델이 필요하지 않습니다. 저장소를 받는 단계에는 네트워크가 필요합니다. Codex 자체의 통신은 별개입니다.

받은 저장소가 다른 위치에 있으면 설치기 경로를 실제 절대 경로로 바꿉니다. 설치한 Skill은 `$clarity-wiki`로 호출하거나 실제 `SKILL.md` 파일을 읽어 적용할 수 있습니다. 자동 인식은 제공 환경에서 확인합니다.

## 두 CLI 검사

과제 작업 폴더에서 실행하는 예시입니다. 파일 경로는 `--root` 기준입니다.

```bash
python3 .agents/skills/clarity-wiki/tools/clarity.py audit --root "$PWD" --original old.txt --revised new.txt
python3 .agents/skills/clarity-wiki/tools/clarity.py evidence --root "$PWD" --manifest manifest.json
```

| 명령 | 확인하는 것 | 한계 |
|---|---|---|
| `audit` | 수치·부호·단위·인용·짧은 대상 문맥의 변경 후보 | 전체 의미·인과·업무 정답은 판단하지 않음 |
| `evidence` | manifest 구조, 파일 존재·비어 있음, 선언된 증거·입력 해시 | 명령을 실행하거나 실행 사실을 인증하지 않음 |

검사는 JSON을 출력합니다. 종료 코드는 `0` 발견 없음, `1` 검토 항목 있음, `2` 잘못된 입력입니다. `no_findings`가 실제 과제의 정확성이나 사람 검토를 보증하지 않습니다. 과제 자체의 실행·테스트·원자료 대조를 먼저 수행합니다.

검사기는 읽기 전용이며 작업 폴더 밖 접근·심볼릭 링크 경로 이탈·과대 입력을 거부합니다. 입력 텍스트는 최대 256 KiB, 근거 파일은 각각 최대 8 MiB, evidence 한 번의 고유 파일은 최대 256개·합계 64 MiB입니다. 상세 형식과 한계는 [로컬 검사 안내](skills/clarity-wiki/references/local-checks.md)에 있습니다.

## 검증과 배포

저장소 루트에서 실행합니다.

```bash
python3 skills/clarity-wiki/tools/validate.py
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

ZIP은 공개 Skill·CLI·설치기·안내·테스트를 포함하며 SHA-256 파일을 함께 만듭니다. 원본 자료·개인 프로필·작업 로그·캐시는 제외합니다. 실제 검증 결과와 적용 범위는 [VERIFICATION](docs/VERIFICATION.md)에 기록합니다.

## 제한된 환경에서 사용

실제 지시서와 최신 운영 안내를 우선합니다. [시험 환경 프로필](skills/clarity-wiki/references/shared/exam-boundaries.md)은 원회차 자료와 재응시에서 새로 확인할 조건을 구분합니다. 사용하는 공개 저장소의 유지 조건과 자료 반출 제한을 확인하고, AI 사용 금지 단계에서는 지원을 중단합니다.

0.4.0은 CLI와 Skill만 배포합니다. 이전 버전에서 호스트에 등록한 서버나 가상환경은 이번 설치기가 변경하지 않으므로 기존 등록은 해당 호스트에서 별도로 정리합니다.

직접 작성한 코드·문서는 MIT 라이선스입니다. 방법론 출처는 [SOURCES](skills/clarity-wiki/SOURCES.md)에 있습니다.
