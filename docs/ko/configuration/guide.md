# 설정 가이드

KToolBox에는 두 가지 설정 계층이 있습니다.

- `.env`, `prod.env` 및 프로세스 변수는 API, 전송, 이름 지정 및 전역 다운로드 동작을 제어합니다.
- `ktoolbox.toml`은 프로젝트 크리에이터 목록과 순서가 있는 게시물 제외 규칙을 저장합니다.

KToolBox는 현재 작업 디렉터리에서 `.env`, 그다음 `prod.env`를 읽습니다. `prod.env` 값은 `.env`의 일치하는 값을 재정의하고 프로세스 환경 변수의 우선순위가 가장 높습니다.

중첩 필드는 이중 밑줄을 사용합니다. 예를 들어 `KTOOLBOX_API__TIMEOUT`은 `config.api.timeout`에 매핑됩니다.

```dotenv
# Pawchive API 요청.
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# 파일 전송.
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# 다운로드 작업.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

모든 설정은 선택 사항입니다. 기본값은 [설정 참조](reference.md)를 확인하세요.

## 설정 생성 또는 편집

현재 모델에서 사용 가능한 모든 dotenv 키를 생성합니다.

```bash
ktoolbox config example
```

선택적 터미널 편집기는 설정 모델 docstring에서 파싱한 필드 설명을 확인할 수 있습니다.

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

선택적 [WebUI](../webui.md)는 형식이 지정된 컨트롤을 통해 동일한 영어와 중국어 간체의 docstring 설명을 제공하며, 최종 값 출처 표시, 비밀 마스킹, 원시 dotenv/TOML 편집, 검증, 차이 미리 보기 및 ETag 충돌 보호를 제공합니다.

편집기를 열지 않고 프로젝트 파일을 확인하거나 검증합니다.

```bash
ktoolbox config path
ktoolbox config validate
```

프로젝트 경로 확인 순서는 전역 `--config`, `KTOOLBOX_PROJECT_CONFIG`, `./ktoolbox.toml`입니다. 쓸 때 같은 디렉터리의 임시 파일과 원자적 교체를 사용하며 TomlKit은 주석을 보존합니다.

## 크리에이터 목록

모든 프로젝트 문서는 `schema_version = 1`로 시작합니다. 크리에이터는 대소문자를 구분하지 않는 `service:id`로 고유하며 선택적 별칭도 고유합니다.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

간단한 목록 항목을 직접 편집하는 대신 `creator add`, `remove`, `enable`, `disable`을 사용하세요. 대상 없는 `sync`는 활성화된 모든 항목을 사용하고, 명시적 별칭이나 식별자는 `enabled`와 관계없이 실행됩니다.

## 게시물 제외 규칙 {#post-blockers}

제외 규칙은 TOML 순서로 실행되며 첫 일치가 게시물을 제외합니다. 전역 규칙은 동기화된 모든 크리에이터에 적용되고 크리에이터 범위는 정확한 `service:id` 값을 나열합니다. 비활성화된 규칙은 설정에 남지만 실행되지 않습니다.

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match`는 재귀적 `any`/`all` 그룹과 그룹 또는 조건의 `negate`를 지원합니다. 조건이 지원하는 연산자:

| 연산자 | 동작 |
| --- | --- |
| `contains` | 선택된 스칼라 중 하나가 설정 값 하나를 포함. |
| `equals` | 선택된 스칼라 중 하나가 설정 값 하나와 같음. |
| `regex` | 선택된 스칼라 중 하나가 정규식 하나와 일치. 패턴은 설정 검증 중 컴파일. |
| `exists` | 선택된 경로가 존재하고 null이 아님. `expected = false`로 기대를 반전. |

`case_sensitive = true`가 아니면 비교는 대소문자를 구분하지 않습니다. 안전한 점 표기 경로에는 `tags[*]`, `file.name`, `attachments[*].name`과 같은 `[*]` 목록 선택자를 포함할 수 있습니다. 없는 경로는 일치하지 않습니다. Python 표현식과 임의 코드는 평가하지 않습니다.

제외 규칙은 상세 정보, 개정판, 디렉터리, 메타데이터 또는 다운로드 작업 전에 목록 응답을 평가합니다. 제외된 게시물과 개정판은 크리에이터 인덱스에 들어가지 않고 일치한 텍스트도 출력되지 않습니다. 비동기 `PostBlocker` 인터페이스와 레지스트리를 통해 동기화 조정자를 변경하지 않고 향후 규칙 형식을 추가할 수 있습니다.

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE`는 사용 중단된 암시적 전역 제목 포함 규칙으로 계속 허용됩니다. KToolBox는 자동으로 다시 작성하지 않으므로 `ktoolbox.toml`로 마이그레이션하세요.

## Pawchive 엔드포인트

v1 기본값은 일반적으로 재정의할 필요가 없습니다.

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY`는 선택 사항이며 파일 다운로더의 요청에만 첨부됩니다. 계정 세션을 지원하지 않는 `PawchiveClient`는 전송하지 않습니다.

## 컬렉션과 경로

dotenv 파일의 집합과 목록에는 JSON 배열을 사용합니다.

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

상대 출력 및 버킷 경로는 작업 디렉터리에서 확인됩니다. 첨부 파일을 각 게시물 디렉터리에 직접 두려면 첨부 파일 경로를 `./`로 설정하세요.

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 이름 지정 템플릿

게시물과 파일 템플릿은 `id`, `user`, `service`, `title`, `added`, `published`, `edited`를 사용할 수 있습니다. 파일 템플릿의 빈 `{}`는 원본 또는 순차 기본 파일 이름을 나타냅니다.

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

`{title:.60}`과 같은 Python 형식 지정 정밀도는 파일 시스템 길이 제한에 유용합니다.

## 다운로드 제한

크기 제한은 바이트 단위이며 파일이 대기열에 들어가기 전에 적용됩니다. 해당 경계를 비활성화하려면 변수를 생략하세요.

```dotenv
# 최소 1 KiB, 최대 1 MiB.
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# 게시물 표지만 가져오고 첨부 파일은 가져오지 않습니다.
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY`는 동시 크리에이터 생산자를 제어합니다. `KTOOLBOX_JOB__COUNT`는 모든 크리에이터가 공유하는 파일 작업자를 별도로 제어합니다.
