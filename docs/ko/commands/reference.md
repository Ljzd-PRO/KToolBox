# 명령 참조

정식 Cyclopts 도움말은 `ktoolbox COMMAND --help`를 실행하여 확인하세요. 명령과 옵션 이름은 하이픈을 사용하며 이전 밑줄 표기도 숨겨진 호환성 명령에서 계속 해석됩니다.

## 전역 옵션

| 옵션 | 의미 |
| --- | --- |
| `-h`, `--help` | 페이저 없이 도움말을 직접 출력합니다. |
| `--version` | 설치된 KToolBox 버전을 출력합니다. |
| `--install-completion` | 감지된 셸에 자동 완성을 설치합니다. |
| `--config PATH` | 프로젝트 파일을 선택합니다. 확인 순서는 이 옵션, `KTOOLBOX_PROJECT_CONFIG`, `./ktoolbox.toml`입니다. |
| `--verbose` | 진단 로그를 포함합니다. |
| `--quiet` | 진행률과 일반 로그를 숨깁니다. |
| `--plain` | 안정적인 줄 단위 진행률을 강제합니다. 비 TTY 출력과 `NO_COLOR`는 이를 자동으로 사용합니다. |
| `--no-color` | ANSI 색상을 비활성화합니다. |

인수 없이 `ktoolbox`를 실행하면 루트 도움말을 출력하고 성공적으로 종료합니다.

## 명령 트리

| 명령 | 용도 |
| --- | --- |
| `download` | 게시물 하나 또는 선택한 개정판을 다운로드합니다. |
| `sync [TARGET ...]` | 명시한 크리에이터를 동기화하거나, 대상이 없으면 활성화된 모든 목록 크리에이터를 동기화합니다. |
| `creator list/add/remove/enable/disable/search` | 목록을 관리하거나 Pawchive 크리에이터를 검색합니다. |
| `post show/search` | 게시물을 조회하거나 크리에이터 게시물을 검색합니다. |
| `config edit/example/validate/path` | 환경 및 프로젝트 설정을 편집하거나 조회합니다. |
| `site-version` | Pawchive 애플리케이션 버전을 출력합니다. |
| `webui [PROJECT_DIR]` | 프로젝트 하나를 위한 선택적 HeroUI 패널을 실행합니다. |

## `download`

Pawchive 게시물 URL 또는 `--service`, `--creator-id`, `--post-id`를 모두 제공합니다.

| 인수 또는 옵션 | 형식 | 기본값 | 의미 |
| --- | --- | --- | --- |
| `POST` | 문자열 | 생략 | Pawchive 게시물 또는 개정판 URL. |
| `--service` | 문자열 | 생략 | 크리에이터 서비스. |
| `--creator-id` | 문자열 | 생략 | 크리에이터 ID. |
| `--post-id` | 문자열 | 생략 | 게시물 ID. |
| `--revision-id` | 문자열 | 생략 | 개정판 목록에서 이 개정판을 선택. |
| `-o`, `--output`, `--path` | 경로 | `.` | 출력 루트. |
| `--dump-post-data` / `--no-dump-post-data` | 불리언 | 활성화 | 검증된 메타데이터를 `post.json`에 저장. |

`download`는 의도적으로 목록 제외 규칙을 적용하지 않습니다.

## `sync`

각 `TARGET`은 Pawchive 크리에이터 URL, `service:id` 또는 목록 별칭일 수 있습니다. 명시적 대상은 목록에서 비활성화되어 있어도 실행됩니다. 대상이 없으면 활성화된 모든 목록 크리에이터를 실행합니다.

| 인수 또는 옵션 | 형식 | 기본값 | 의미 |
| --- | --- | --- | --- |
| `TARGET ...` | 문자열 | 활성화된 목록 | 0명 이상의 크리에이터. |
| `--service` + `--creator-id` | 문자열 | 생략 | 명시적 크리에이터 한 명 추가. 두 값을 함께 제공해야 함. |
| `-o`, `--output`, `--path` | 경로 | `.` | 출력 루트. |
| `--save-creator-indices` | 불리언 | 비활성화 | 성공적으로 생산한 후 크리에이터 인덱스를 원자적으로 저장. |
| `--mix-posts` / `--no-mix-posts` | 불리언 | 환경 설정 | `job.mix_posts` 재정의. |
| `--start-time`, `--start` | 날짜 | 생략 | 게시 날짜의 포함 하한, `YYYY-MM-DD`. |
| `--end-time`, `--end` | 날짜 | 생략 | 게시 날짜의 포함 상한, `YYYY-MM-DD`. |
| `--offset` | 정수 | `0` | 첫 게시물 인덱스. |
| `--length` | 정수 | 모두 | 크리에이터별 최대 허용 게시물 수. |
| `--keywords` | 반복 문자열 | 환경 설정 | 값 중 하나를 포함하는 제목 포함. |
| `--keywords-exclude` | 반복 문자열 | 환경 설정 | 사용 중단된 제목 제외 호환성 입력. |

`job.creator_concurrency`는 크리에이터 생산을 제한하고 `job.count`는 공유 파일 작업자를 제한합니다.

## `creator`

| 명령 | 인수와 옵션 | 의미 |
| --- | --- | --- |
| `creator list` | `--json` | 목록 항목을 Rich 표 또는 JSON으로 표시. |
| `creator add TARGET` | `--alias NAME`, `--disabled` | URL 또는 `service:id` 추가. |
| `creator remove TARGET` | | 별칭, URL 또는 식별자로 삭제. |
| `creator enable TARGET` | | 저장된 크리에이터 활성화. |
| `creator disable TARGET` | | 저장된 크리에이터 비활성화. |
| `creator search` | `--name`, `--creator-id`/`--id`, `--service`, `--dump`, `--json` | 공개 크리에이터 목록 필터링. |

## `post`

| 명령 | 인수와 옵션 | 의미 |
| --- | --- | --- |
| `post search` | `--creator-id`/`--id`, `--name`, `--service`, `-q`/`--query`, `-o`/`--offset`, `--dump`, `--json` | 선택한 크리에이터의 게시물 검색. 직접 API 쿼리는 3자 이상이며 API 오프셋은 50으로 나누어짐. |
| `post show SERVICE CREATOR_ID POST_ID [REVISION_ID]` | `--dump`, `--json` | 현재 게시물 메타데이터 또는 선택한 개정판 표시. |

`--json`이 없으면 쿼리 명령은 의도적으로 터미널 표에서 게시물 본문을 생략합니다.

## `config`

| 명령 | 의미 |
| --- | --- |
| `config path` | 확인된 프로젝트 경로를 줄 바꿈 없이 출력. |
| `config validate` | 스키마 버전, 크리에이터 고유성, 제외 규칙 형식, 범위, 조건 및 정규식 검증. |
| `config example` | 설정 모델 docstring에서 모든 dotenv 설정 렌더링. |
| `config edit` | 선택적 Urwid 편집기를 열고 저장 전에 검증. |

## `webui`

이 명령을 사용하기 전에 `ktoolbox[webui]`를 설치하세요. 기본 명령은 프로젝트 디렉터리를 받고, `ktoolbox.toml`이 없으면 경고 후 생성합니다. 유효한 단일 계정 자격 증명은 여전히 필요합니다.

| 인수 또는 옵션 | 기본값 | 의미 |
| --- | --- | --- |
| `PROJECT_DIR` | `.` | 이 프로세스가 제공하는 고정 동기화 프로젝트. |
| `--host` | `webui.host` | 수신 인터페이스 재정의. |
| `--port` | `webui.port` | TCP 포트 재정의. |
| `--no-open` | 비활성화 | 기본 브라우저에서 로컬 URL을 열지 않음. |
| `webui hash-password` | | 숨겨진 터미널 입력으로 두 번 묻고 Argon2id 해시 출력. |

내장 서버는 HTTP 보안 경고를 출력합니다. localhost 외부에 노출하기 전에 [WebUI 가이드](../webui.md)를 참조하세요.

## 호환성 별칭

이 별칭은 도움말에서 숨겨지고 호출할 때마다 사용 중단 경고를 한 번 표시합니다.

| 이전 이름 | 대체 이름 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

## 종료 코드와 스트림

| 코드 | 의미 |
| --- | --- |
| `0` | 성공. |
| `1` | 여러 크리에이터의 부분 성공을 포함한 원격, 크리에이터 또는 다운로드 실패. |
| `2` | 잘못된 인수 또는 설정. |
| `130` | 사용자 중단. |

표와 JSON은 stdout을 사용합니다. 로그, 진행률, 경고 및 오류는 stderr를 사용합니다.
