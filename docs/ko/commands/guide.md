# 명령 가이드

KToolBox는 일반적인 하이픈 옵션과 Rich 도움말이 있는 Cyclopts 명령을 사용합니다. 도움말은 직접 출력되며 페이저를 열지 않습니다.

```bash
ktoolbox --help
ktoolbox sync --help
```

![KToolBox 명령 개요](../../assets/cli-overview.png)

전역 옵션은 명령 앞이나 뒤에 올 수 있습니다.

```bash
ktoolbox --config ./ktoolbox.toml --plain sync
ktoolbox creator list --json --config ./ktoolbox.toml
```

진단 로그에는 `--verbose`, 진행률과 일반 로그를 숨기려면 `--quiet`, 안정적인 줄 단위 진행률에는 `--plain`, ANSI 색상 없이 대화형 레이아웃을 유지하려면 `--no-color`를 사용합니다.

## 게시물 하나 다운로드

Pawchive 페이지 URL 또는 세 가지 식별 값을 전달합니다.

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

ktoolbox download \
  --service fanbox \
  --creator-id 6570768 \
  --post-id 1836570 \
  --output downloads
```

`--revision-id`를 사용하여 개정판 하나를 선택합니다. Pawchive에는 단일 개정판 상세 엔드포인트가 없으므로 KToolBox는 개정판 목록을 가져와 해당 ID를 일치시킵니다. 현재 게시물을 다운로드할 때 모든 개정판을 포함하려면 `KTOOLBOX_JOB__INCLUDE_REVISIONS=True`를 설정하세요.

중단 후 동일한 명령을 다시 실행하세요. 완료된 파일은 건너뛰고 호환되는 임시 파일은 HTTP Range 요청으로 재개합니다. 명시적 `download`는 동기화 제외 규칙을 적용하지 않습니다.

## 크리에이터 동기화

`sync`는 원하는 수의 크리에이터 URL, `service:id` 식별자 또는 프로젝트 목록에 저장된 별칭을 받습니다.

```bash
# 제한된 크리에이터 한 명 동기화.
ktoolbox sync fanbox:123 --length 1

# 여러 크리에이터가 하나의 동시 다운로드 풀을 공유합니다.
ktoolbox sync fanbox:123 patreon:456 studio-c --length 10
```

`--length`를 생략하면 사용 가능한 모든 페이지를 따릅니다. CLI 경계에서 `--offset`은 게시물 인덱스이며 KToolBox가 Pawchive의 50개 단위 페이지 오프셋으로 변환합니다.

```bash
ktoolbox sync fanbox:123 --offset 10 --length 5
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

각 크리에이터는 `Creator name [service-creator_id]`로 저장됩니다. 크리에이터 생산자는 한 번에 최대 `job.creator_concurrency`개가 실행됩니다. 제한된 큐는 하나의 공정한 라운드 로빈 스케줄러로 들어가며 `job.count`가 파일 전송 동시성을 제어합니다. 모든 크리에이터를 기다리지 않고 첫 작업이 생기는 즉시 다운로드를 시작합니다.

크리에이터 한 명이 실패해도 다른 크리에이터의 완료된 작업은 버리지 않습니다. 실패한 크리에이터는 이전 인덱스를 유지하고 최종 명령은 요약을 출력한 후 상태 `1`로 종료합니다.

## 목록 관리

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add https://pawchive.pw/patreon/user/456 --alias studio-b
ktoolbox creator disable studio-b
ktoolbox creator list
ktoolbox creator enable studio-b
ktoolbox creator remove studio-b
```

대상 없이 `ktoolbox sync`를 실행하면 활성화된 모든 목록 항목을 동기화합니다. 명시적으로 지정한 비활성 크리에이터는 계속 실행됩니다. `service:id` 식별자는 고유해야 하며 별칭은 선택 사항이지만 제공하는 경우 고유해야 합니다. 설정을 쓸 때 주석을 보존합니다.

## 작품이 아닌 게시물 제외

`ktoolbox.toml`에 순서가 있는 필드 제외 규칙을 정의합니다. 규칙은 전역 또는 선택한 `service:id` 크리에이터에만 적용할 수 있으며 제목, 내용, 태그, 파일 이름, ID 및 중첩 목록 경로를 검사할 수 있습니다. 첫 번째로 일치하는 규칙은 상세 정보, 개정판, 메타데이터, 디렉터리 또는 다운로드 작업을 만들기 전에 게시물을 제외합니다.

전체 예제는 [설정 가이드](../configuration/guide.md#post-blockers)를 참조하세요. `KTOOLBOX_JOB__KEYWORDS_EXCLUDE`는 마이그레이션 전용의 사용 중단된 전역 제목 제외 규칙으로 남아 있습니다.

## 공개 데이터 조회

```bash
ktoolbox creator search --name example --service fanbox
ktoolbox post search --creator-id 6570768 --service fanbox --query preview --offset 0
ktoolbox post show fanbox 6570768 1836570
```

쿼리 명령은 기본적으로 간결한 Rich 표를 사용합니다. 기계가 읽을 수 있는 stdout에는 `--json`을 추가하세요. 로그와 진행률은 stderr에 유지됩니다. `--dump path.json`은 검증된 모델을 파일에도 씁니다.

## 설정 유틸리티

```bash
ktoolbox config path
ktoolbox config validate
ktoolbox config example
ktoolbox config edit
ktoolbox site-version
```

편집기에는 선택적 `urwid` 종속성이 필요합니다. dotenv 설정과 목록/제외 규칙 프로젝트 문서를 모두 편집한 다음 저장하기 전에 검증합니다.

## 선택적 프로젝트 패널 실행

`ktoolbox[webui]`를 설치하고 계정을 설정한 후 패널을 프로젝트 디렉터리에 바인딩합니다. `ktoolbox.toml`이 없으면 터미널 경고 후 자동으로 생성됩니다.

```bash
ktoolbox webui . --host 127.0.0.1
```

패널은 동일한 다운로드, 동기화, 목록, 제외 규칙, 쿼리 및 설정 흐름을 영구 작업 진행률과 제어가 있는 관리형 프로젝트 작업으로 제공합니다. 네트워크 인터페이스에서 수신하기 전에 [WebUI 가이드](../webui.md)를 확인하세요.

## 종료 상태

| 코드 | 의미 |
| --- | --- |
| `0` | 명령이 성공적으로 완료되었습니다. |
| `1` | 원격 작업, 크리에이터 또는 파일 다운로드 실패. 부분 파일은 유지됩니다. |
| `2` | 인수 또는 설정이 잘못되었습니다. |
| `130` | 사용자가 명령을 중단했습니다. |

예상된 실패는 Python 트레이스백 없이 출력됩니다.
