# 설정 참조

환경 변수 이름은 `KTOOLBOX_`로 시작하고 중첩 모델 필드를 `__`로 연결합니다. `path`, `set`, `list`로 표시된 형식은 Pydantic이 파싱합니다. dotenv의 컬렉션에는 JSON 배열을 사용하세요.

## 루트

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `ssl_verify` | 불리언 | `True` | API 및 다운로드 요청의 TLS 인증서 검증. |
| `json_dump_indent` | 정수 | `4` | JSON 출력에 사용하는 들여쓰기. |
| `use_uvloop` | 불리언 | `True` | 설치된 경우 Unix에서 uvloop, Windows에서 winloop 사용. |

## `api`

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | API URL 스킴. |
| `netloc` | 문자열 | `pawchive.pw` | API 호스트. |
| `statics_netloc` | 문자열 | `pawchive.pw` | 정적 크리에이터 자산 호스트. |
| `path` | 문자열 | `/api/v1` | API 루트 경로. |
| `timeout` | 실수 | `5.0` | 요청별 시간 초과(초). |
| `retry_times` | 정수 | `3` | 전송, `429`, `5xx` 실패에 대한 추가 시도. |
| `retry_interval` | 실수 | `2.0` | API 시도 사이의 지연(초). |

API 그룹에는 의도적으로 세션 키가 없습니다.

## `downloader`

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `scheme` | `http` / `https` | `https` | 파일 URL 스킴. |
| `files_netloc` | 문자열 | `file.pawchive.pw` | Pawchive 파일 호스트. |
| `file_path_prefix` | 문자열 | `/data` | API 파일 경로 앞에 추가할 접두사. |
| `session_key` | 문자열 | 비어 있음 | 파일 요청에만 전송하는 선택적 쿠키. |
| `timeout` | 실수 | `30.0` | 파일 요청 시간 초과(초). |
| `encoding` | 문자열 | `utf-8` | 이름과 추출 텍스트의 인코딩. |
| `buffer_size` | 정수 | `20480` | 버퍼 파일 I/O 크기(바이트). |
| `chunk_size` | 정수 | `1024` | 스트림 청크 크기(바이트). |
| `temp_suffix` | 문자열 | `tmp` | 완료되지 않은 다운로드의 접미사. |
| `retry_times` | 정수 | `10` | 추가 다운로드 시도 횟수. |
| `retry_stop_never` | 불리언 | `False` | `retry_times`를 무시하고 계속 재시도. |
| `retry_interval` | 실수 | `3.0` | 다운로드 시도 사이의 지연(초). |
| `tps_limit` | 실수 | `5.0` | 초당 새 연결의 최대 수. |
| `use_bucket` | 불리언 | `False` | 콘텐츠 주소 기반 로컬 하드 링크 저장소 활성화. |
| `bucket_path` | 경로 | `.ktoolbox/bucket_storage` | 로컬 버킷 디렉터리. |
| `reverse_proxy` | 문자열 | `{}` | 다운로드 URL 템플릿. `{}`를 원본 URL로 교체. |
| `keep_metadata` | 불리언 | `True` | 가능한 경우 원격 수정 메타데이터 보존. |

대상 파일 시스템이 하드 링크를 만들 수 없으면 버킷 모드가 자동으로 비활성화됩니다.

## `job.post_structure`

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `attachments` | 경로 | `attachments` | 첨부 파일 하위 디렉터리. 게시물 루트에는 `./` 사용. |
| `content` | 경로 | `content.txt` | 추출한 본문 파일. |
| `external_links` | 경로 | `external_links.txt` | 추출한 외부 링크 파일. |
| `file` | 문자열 | `{id}_{}` | 표지 파일 이름 템플릿. |
| `revisions` | 경로 | `revisions` | 개정판 하위 디렉터리. |

## `job`

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `count` | 정수 | `4` | 동시 다운로드 작업자. |
| `creator_concurrency` | 정수 | `4` | 공유 파일 작업자에 공급하는 동시 크리에이터 생산자. |
| `include_revisions` | 불리언 | `False` | 현재 게시물의 알려진 모든 개정판 포함. |
| `post_dirname_format` | 문자열 | `{title}` | 게시물별 디렉터리 템플릿. |
| `mix_posts` | 불리언 | `False` | 게시물 디렉터리 없이 모든 크리에이터 파일을 함께 저장. |
| `sequential_filename` | 불리언 | `False` | 첨부 파일을 숫자 순서로 이름 변경. |
| `sequential_filename_excludes` | 집합 | 비어 있음 | 원래 이름을 유지할 확장자. |
| `filename_format` | 문자열 | `{}` | 첨부 파일 이름 템플릿. |
| `allow_list` | 집합 | 비어 있음 | 포함할 Unix 셸 파일 이름 패턴. |
| `block_list` | 집합 | 비어 있음 | 제외할 Unix 셸 파일 이름 패턴. |
| `extract_content` | 불리언 | `False` | 게시물 텍스트를 별도로 저장. |
| `extract_content_images` | 불리언 | `False` | 게시물 본문에서 참조한 이미지 다운로드. |
| `extract_external_links` | 불리언 | `False` | 본문에서 일치하는 외부 링크 저장. |
| `external_link_patterns` | 목록 | 내장 | 외부 링크 추출에 사용하는 정규식. |
| `group_by_year` | 불리언 | `False` | 게시물 디렉터리를 게시 연도별로 그룹화. |
| `group_by_month` | 불리언 | `False` | 월별 그룹화. 연도 그룹화 필요. |
| `year_dirname_format` | 문자열 | `{year}` | 연도 디렉터리 템플릿. |
| `month_dirname_format` | 문자열 | `{year}-{month:02d}` | 월 디렉터리 템플릿. |
| `keywords` | 집합 | 비어 있음 | 포함할 대소문자 무시 제목 용어. |
| `keywords_exclude` | 집합 | 비어 있음 | 사용 중단된 제목 제외. 암시적 전역 규칙으로 변환. |
| `download_file` | 불리언 | `True` | 일반적으로 표지인 기본 게시물 파일 다운로드. |
| `download_attachments` | 불리언 | `True` | 첨부 파일 다운로드. |
| `min_file_size` | 정수 / 생략 | 생략 | 이 바이트 수보다 작은 파일 건너뛰기. |
| `max_file_size` | 정수 / 생략 | 생략 | 이 바이트 수보다 큰 파일 건너뛰기. |

이름 템플릿은 `id`, `user`, `service`, `title`, `added`, `published`, `edited`를 받습니다. 연도 및 월 템플릿은 `year`와 `month`를 받습니다.

## 프로젝트 `ktoolbox.toml`

프로젝트 문서는 환경 설정과 별개입니다. 경로는 전역 `--config`, `KTOOLBOX_PROJECT_CONFIG`, `./ktoolbox.toml` 순서로 확인됩니다.

### 루트

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `schema_version` | 리터럴 `1` | `1` | 프로젝트 스키마 버전. 다른 값은 거부. |
| `creators` | 테이블 배열 | 비어 있음 | 저장된 크리에이터 목록. |
| `blockers` | 테이블 배열 | 비어 있음 | 순서가 있는 제외 규칙 사양. |

### 크리에이터 항목

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `service` | 비어 있지 않은 문자열 | 필수 | Pawchive 서비스. |
| `creator_id` | 비어 있지 않은 문자열 | 필수 | Pawchive 크리에이터 ID. |
| `alias` | 문자열 / 생략 | 생략 | 고유한 CLI 대상. `:` 금지. |
| `enabled` | 불리언 | `True` | 대상 없는 `sync`에 포함. |

### 제외 규칙 항목

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `id` | 식별자 | 필수 | 문자, 숫자, `.`, `_`, `-`로 구성된 고유 ID. |
| `type` | 문자열 | `field-match` | 등록된 구현. 알 수 없는 형식은 거부. |
| `enabled` | 불리언 | `True` | 이 규칙의 평가 참여 여부. |
| `scope.mode` | `global` / `creators` | `global` | 전역 또는 선택한 식별자에 적용. |
| `scope.creators` | `service:id` 목록 | 비어 있음 | 크리에이터 범위에서 필수 및 비어 있지 않아야 하며 전역 범위에서 금지. |
| `options.rule` | 조건 그룹 | `field-match`에 필수 | 루트 재귀 규칙. |

조건 그룹은 `kind = "group"`, `mode = "any"` 또는 `"all"`, 비어 있지 않은 `conditions` 목록과 선택적 `negate`를 사용합니다. 필드 조건은 `kind = "field"`, 안전한 점 표기 `field`, `contains`, `equals`, `regex`, `exists` 중 하나와 선택적 `case_sensitive`, `negate`, `expected`를 사용합니다. `exists`가 아닌 연산자는 비어 있지 않은 `values` 목록이 필요하고 `exists`는 `values`를 금지합니다.

## `webui`

이 설정은 `ktoolbox[webui]`를 설치한 경우에만 사용하며 시작에는 필수가 아닙니다. 빈 사용자 이름은 `admin`이 되고 두 암호가 모두 비어 있으면 서버가 무작위 암호를 생성하여 유효 자격 증명을 터미널에 출력하고 해당 프로세스에서만 유지합니다.

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `host` | 문자열 | `0.0.0.0` | HTTP 수신 인터페이스. 신뢰할 수 있는 LAN 외부에서는 `127.0.0.1` 권장. |
| `port` | 정수 | `8789` | 1~65535 범위의 HTTP 수신 포트. |
| `open_browser` | 불리언 | `True` | 시작 후 로컬 패널 URL 열기. |
| `username` | 문자열 | 비어 있음 | 선택 사항이며 비어 있으면 `admin`을 사용합니다. |
| `password_hash` | 비밀 문자열 | 비어 있음 | 권장 고정 Argon2id 해시. |
| `password` | 비밀 문자열 | 비어 있음 | 일반 텍스트 대체 값이며 둘 다 비면 시작 시 생성합니다. |
| `max_active_tasks` | 정수 | `2` | 동시 최상위 작업 수, 1~16. |
| `session_idle_hours` | 정수 | `24` | 마지막 사용부터 측정한 세션 만료. |
| `session_absolute_hours` | 정수 | `168` | 로그인부터 측정한 최대 세션 수명. |

모든 이름은 일반 접두사를 사용합니다. 예: `KTOOLBOX_WEBUI__PASSWORD_HASH`. `ktoolbox webui hash-password`로 해시를 생성하고 Argon2 해시에는 `$` 문자가 있으므로 dotenv에서 따옴표로 묶으세요. 명령줄 `--host`, `--port`, `--no-open`은 한 번의 시작에 해당 설정을 재정의합니다.

## `logger`

| 필드 | 형식 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `path` | 경로 / 생략 | 생략 | 로그 파일 경로. 생략하면 파일 로깅 비활성화. |
| `level` | 문자열 / 정수 | `DEBUG` | 최소 로그 수준. |
| `rotation` | 문자열 / 정수 / 시간 | `1 week` | Loguru 순환 조건. |
