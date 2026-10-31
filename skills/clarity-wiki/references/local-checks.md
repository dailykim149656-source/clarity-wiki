# 로컬 검사와 manifest v1

직접 CLI는 Python 3.10 이상과 POSIX 경로 접근을 지원하는 macOS/Linux에서 표준 라이브러리로 동작한다. `<SKILL_DIR>`와 `<WORKSPACE>`를 각각 실제 절대 경로로 바꾼다. 입력 파일은 작업 공간에 있어야 한다. evidence 한 번에 고유 파일 최대 256개·합계 64 MiB까지 읽는다.

```sh
python3 '<SKILL_DIR>/tools/clarity.py' audit --root '<WORKSPACE>' --original old.txt --revised new.txt --limit 5
python3 '<SKILL_DIR>/tools/clarity.py' evidence --root '<WORKSPACE>' --manifest manifest.json --limit 5
python3 '<SKILL_DIR>/tools/validate.py'
```

`audit`와 `evidence`는 stdout에 JSON을 출력한다. 종료 코드는 `0` 경고 없음, `1` 발견 항목 있음, `2` 잘못된 입력이다. `--limit`는 1–30이며 표시가 잘려도 전체 건수와 잘림 여부를 확인한다. `validate.py`는 별도의 구조 검사다. 설치형 `clarity-wiki`도 같은 두 하위 명령과 인자를 쓴다.

## 수치의 대상 문맥

`audit`는 같은 줄에서 수치 바로 앞의 짧은 대상 문맥도 비교한다. `A10건`, `A 10건`, `A: 10건`, `A=10건` 형식에서 같은 수치에 붙은 대상이 바뀌면 `NUMBER_CONTEXT_CHANGED` 후보를 반환한다. `장비A: 10건, 장비B: 20건`을 `장비B: 10건, 장비A: 20건`으로 바꾼 경우가 해당한다. 대상·수치가 같고 구분자·공백만 바뀌면 그 표기만으로 경고하지 않는다.

전체 문장이나 표의 키를 해석하는 검사는 아니다. 여러 단어로 된 대상의 마지막 부분이 같거나 대상과 값이 다른 줄에 있으면 놓칠 수 있다. 재정렬·긴 대상명·모호한 정렬은 원자료와 키별 값·단위를 직접 대조한다.

## manifest

작업 공간 기준 상대 경로로 작성한다. 실제 검증을 수행한 뒤 로그와 검증에 사용한 입력·코드 파일의 SHA-256을 기록한다. 해시는 64자리 소문자 16진수다.

```json
{
  "version": 1,
  "artifacts": ["result.csv"],
  "requirements": [{
    "id": "R1",
    "criterion": "입력 값의 합계를 결과 파일에 저장한다",
    "status": "unverified",
    "evidence": []
  }]
}
```

상태는 `verified`, `unverified`, `blocked` 중 하나다. `verified`의 각 근거에는 `path`, `sha256`, `command`, `exit_code`, `inputs`를 기록한다. `inputs`는 `path`와 `sha256`을 가진 객체의 배열이다. 성공 근거와 입력 스냅샷이 없는 `verified`는 불완전하다. 미검증 상태를 없애기 위해 실행하지 않은 명령이나 성공 로그를 만들지 않는다.

**`evidence`는 증거 구조·선언된 해시 검사다.** `artifacts`에 경로만 나열한 파일은 존재 여부와 비어 있지 않은지만 확인하며, 내용 변경은 판정하지 않는다. 산출물을 실제 검증에서 읽었다면 해당 파일도 근거의 `inputs`에 `{"path":"result.csv","sha256":"<실제 검증 시점의 64자리 해시>"}`로 연결한다. 이후 변경은 `stale_input`으로 감지한다. 산출물 자체가 근거인 경우에는 `evidence.path`와 `evidence.sha256`으로 연결할 수 있다. 실제 검증 뒤에 읽은 파일의 해시를 기록하며, 해시만 갱신해서 재검증을 대신하지 않는다.

[합성 manifest](../examples/evidence/manifest.json)는 [합성 입력](../examples/evidence/input.csv), [합성 산출물](../examples/evidence/result.csv), [예시 로그](../examples/evidence/verification.txt)를 연결한다. **서식 학습용으로 작성한 합성 기록**이며 실제 작업을 검증했다는 증거가 아니다. 예제 자체의 구조 점검:

```sh
python3 '<SKILL_DIR>/tools/clarity.py' evidence --root '<SKILL_DIR>/examples/evidence' --manifest manifest.json --limit 5
```

이 예제가 경고 없이 통과해도 명령이 실제 실행됐다는 뜻이 아니다. 검사기는 명령·상태를 입력자의 주장으로 취급한다.

## 결과 해석

- audit의 변경 후보는 원문/수정문 위치와 토큰을 직접 대조한다. 단순 표기 차이는 검토 후 판별하고, 문맥 정렬이 모호하면 의미가 같다고 단정하지 않는다.
- evidence의 누락·빈 파일·해시 불일치는 해당 파일과 실제 검증 기록을 확인한다. 입력 변경 후 오래된 로그라면 관련 검증을 다시 실행한다. 해시만 새 값으로 바꾸어 검증한 것처럼 만들지 않는다.
- 해시는 기록한 파일의 변경 여부만 확인한다. 누락한 의존 파일, 조작한 로그, 거짓 명령·종료 코드, 사람이 확인했다는 주장을 입증하지 않는다.
- `no_findings`는 의미 정확성, 업무 정답, 실험 재현 또는 사람 검토를 보장하지 않는다.

CLI 불가 시 수동 대조를 사용하고 자동 검사 미수행을 기록한다. 수동 확인 기록은 성공한 명령 로그로 꾸미지 않는다.
