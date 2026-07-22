# v1로 마이그레이션

KToolBox v1은 백엔드와 라이브러리 API에 호환되지 않는 변경을 포함하는 릴리스입니다.

## 업그레이드 전

1. `.env` 또는 `prod.env` 파일을 백업합니다.
2. 실행 중인 v0 다운로드를 완료하거나 취소합니다.
3. 전체 동기화 전에 `--length=1`로 크리에이터 한 명을 제한하여 테스트합니다.

## 필수 변경 사항

| v0 동작 | v1 동작 |
| --- | --- |
| Kemono/Coomer 엔드포인트 | Pawchive만 지원 |
| Python 3.8+ | Python 3.10-3.14 |
| `KTOOLBOX_API__SESSION_KEY` | `KTOOLBOX_DOWNLOADER__SESSION_KEY` |
| API 설정에 API와 파일 호스트가 혼합됨 | API/정적 호스트는 `api`, 파일 호스트는 `downloader` |
| 개정 상세 정보 요청 | 개정 목록을 가져온 다음 `revision_id`로 선택 |
| `.data.post` 같은 래퍼 응답 | 형식이 지정된 `Post`, `Revision` 및 기타 Pydantic 모델을 직접 반환 |
| Python Fire 명령 인터페이스 | 하이픈 옵션과 명시적 종료 코드가 있는 Cyclopts 명령 트리 |
| 동기화마다 크리에이터 한 명 | 원하는 수의 대상 또는 활성화된 프로젝트 목록 |
| 전역 `keywords_exclude`만 지원 | 순서가 있는 전역 및 크리에이터 범위 `field-match` 제외 규칙 |

새 기본값은 다음과 같습니다.

```dotenv
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

## CLI 명령

숨겨진 별칭은 기존 자동화를 일시적으로 계속 실행할 수 있게 하지만 호출할 때마다 사용 중단 경고를 출력합니다.

| v0 명령 | v1 명령 |
| --- | --- |
| `download-post` | `download` |
| `sync-creator` | `sync` |
| `search-creator` | `creator search` |
| `search-creator-post` | `post search` |
| `get-post` | `post show` |
| `config-editor` | `config edit` |
| `example-env` | `config example` |

옵션은 Python 스타일 밑줄이 아닌 `--creator-id`로 표시됩니다. 호환성 별칭에서는 이전 밑줄 표기도 계속 사용할 수 있습니다. 도움말은 직접 출력되며 더 이상 페이저를 종료할 필요가 없습니다.

CLI 실패는 프로세스 상태를 사용합니다. `0`은 성공, `1`은 원격/크리에이터/다운로드 실패, `2`는 인수/설정 실패, `130`은 중단입니다. JSON과 표는 stdout을, 진행률과 로그는 stderr를 사용합니다.

## 프로젝트 목록과 제외 규칙

재사용 가능한 목록이나 구조화된 제외 규칙이 필요한 경우에만 `ktoolbox.toml`을 만드세요. 파일이 없는 상태는 유효한 빈 프로젝트입니다.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true
```

비어 있지 않은 `KTOOLBOX_JOB__KEYWORDS_EXCLUDE` 값을 전역 `field-match` 제목 조건으로 옮기세요. 이전 설정은 암시적 제외 규칙으로 계속 작동하며 경고를 표시하지만 KToolBox는 로컬 파일을 다시 작성하지 않습니다. [설정 가이드](configuration/guide.md#post-blockers)를 참조하세요.

`KTOOLBOX_JOB__CREATOR_CONCURRENCY`의 기본값은 `4`이며 크리에이터 생산자 수를 제한합니다. 기존 `KTOOLBOX_JOB__COUNT`는 파일 작업자 수를 계속 제한합니다.

## 선택적 WebUI

v1은 새로운 HeroUI 패널을 추가하며 이전 실험적 `webui` 브랜치를 마이그레이션하거나 재사용하지 않습니다. `ktoolbox[webui]`를 설치하고 프로젝트를 선택하세요. `ktoolbox.toml`은 경고 후 자동 생성됩니다. 계정이 없으면 시작마다 `admin`과 새 무작위 암호를 출력하며, 고정 자격 증명이 필요할 때 단일 계정을 설정합니다.

```bash
ktoolbox webui hash-password
ktoolbox webui /path/to/project --host 127.0.0.1
```

`.env`와 `prod.env`는 이제 버전 관리되는 예제가 아니라 무시되는 로컬 파일입니다. 자격 증명과 다운로더 세션은 여기에 보관하고 `example.env`를 공개 템플릿으로 사용하며, 업그레이드 전에 이전에 추적된 dotenv 파일을 점검하세요. WebUI는 `.ktoolbox/webui.sqlite3`와 프로젝트 잠금을 만들지만 둘 다 CLI 다운로드 출력 형식을 변경하지 않습니다.

HTTP 배포 위험과 영구 작업 동작은 [WebUI 가이드](webui.md)를 참조하세요.

## 라이브러리 API

이전 `BaseAPI`, 클래스 호출기, 모듈 수준 `get_*` 함수, `APIRet` 및 Kemono 응답 래퍼는 호환성 별칭 없이 제거되었습니다. 인스턴스를 생성한 비동기 클라이언트를 사용하세요.

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

성공한 호출은 Pydantic v2 모델을 반환합니다. 실패하면 형식이 지정된 `PawchiveError` 하위 클래스가 발생합니다. [API 문서](api.md)를 참조하세요.
