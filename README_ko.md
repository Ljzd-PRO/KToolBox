<div align="center">

# KToolBox

[Pawchive](https://pawchive.pw/)의 공개 게시물을 다운로드하기 위한 비동기 CLI, HeroUI 관리 패널 및 Python 클라이언트입니다.

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/ko/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

KToolBox v1은 Pawchive만 백엔드로 지원합니다. Pawchive OpenAPI 문서의 모든 공개 작업에 형식이 지정된 접근을 제공하며, 계정 인증이 필요한 즐겨찾기 작업은 지원 범위에서 제외합니다.

## 기능

- 게시물 하나를 다운로드하거나 하나의 명령으로 원하는 수의 크리에이터를 동기화합니다.
- 프로젝트 로컬 `ktoolbox.toml`에서 재사용 가능하고 활성화/비활성화할 수 있는 크리에이터 목록을 관리합니다.
- 순서가 있는 전역 또는 크리에이터별 필드 제외 규칙으로 작품이 아닌 게시물을 제외합니다.
- 여러 API 작업에서 하나의 형식 지정 비동기 `PawchiveClient`를 재사용합니다.
- HTTP Range 요청으로 부분 다운로드를 재개하고 기존 파일을 건너뜁니다.
- 파일 크기 제한, 확장자 선택, 제목과 날짜 필터링, 표지와 첨부 파일 다운로드를 개별 제어합니다.
- 디렉터리 구조, 게시물 이름, 파일 이름, 순차 이름 및 연/월 그룹화를 사용자 지정합니다.
- 게시물 메타데이터, 크리에이터 색인, 추출한 본문, 본문 이미지 및 일치하는 외부 링크를 저장합니다.
- 동시에 처리되는 크리에이터의 작업을 하나의 공정한 다운로드 풀로 스트리밍하고, 파일별 속도와 전체 처리량을 안정적인 Rich 진행률로 표시합니다.
- 7개 언어를 지원하는 반응형 HeroUI 패널에서 영구 작업, 실시간 진행률, 설정 양식, 크리에이터 및 제외 규칙 편집, 라이트/다크 테마와 함께 하나의 동기화 프로젝트를 관리합니다.
- MockTransport 기반의 완전한 오프라인 테스트 모음을 사용하며 우발적인 네트워크 접근을 차단합니다.

## 요구 사항

- Python 3.10~3.14
- Windows, macOS 또는 Linux

## 설치

`pipx` 사용을 권장합니다.

```bash
pipx install ktoolbox
```

이벤트 루프 최적화 및 터미널 설정 편집기를 위한 선택적 종속성:

```bash
# Windows
pipx install "ktoolbox[urwid,winloop]" --force

# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force
```

선택적 WebUI 런타임 설치:

```bash
pipx install "ktoolbox[webui]" --force
```

## 빠른 시작

명령 도움말 표시:

```bash
ktoolbox -h
ktoolbox download -h
```

![KToolBox 명령 개요](docs/assets/cli-overview.png)

게시물 하나 다운로드:

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
```

첫 실행을 게시물 하나로 제한하여 크리에이터 한 명 동기화:

```bash
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

오프셋, 날짜 범위 또는 제목 필터 사용:

```bash
ktoolbox sync fanbox:123 patreon:456 --length 10
ktoolbox sync fanbox:123 --start-time 2025-01-01 --end-time 2025-03-01
```

자주 동기화하는 크리에이터를 저장한 다음 대상 없이 `sync` 실행:

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

다시 실행하면 기존 파일을 건너뜁니다. 파일 호스트가 Range를 지원하면 완료되지 않은 임시 파일부터 다운로드를 재개합니다.

## WebUI

WebUI는 `ktoolbox.toml`이 포함된 하나의 프로젝트 디렉터리에 연결됩니다. 가능하면 Argon2id 해시를 사용하여 단일 계정을 설정하세요.

```bash
ktoolbox webui hash-password
```

출력된 해시와 계정 이름을 프로젝트의 `.env`에 추가한 다음 패널을 시작합니다.

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

```bash
ktoolbox webui /path/to/project
```

![KToolBox WebUI 설정](docs/assets/webui/09-configuration-light.png)

전체 인터페이스는 중국어 간체, 중국어 번체, 영어, 일본어, 한국어, 프랑스어, 러시아어를 지원합니다. 처음에는 브라우저 언어를 따르며, 수동 선택은 저장되고 날짜, 숫자, 정렬, 설정 설명, 입력 검증 및 서버 오류도 함께 전환됩니다.

작업 행은 오프라인 표시 스냅샷에 읽기 쉬운 게시물 제목과 크리에이터 이름을 보존합니다. 데스크톱과 모바일 레이아웃에서 세부 정보, 수명 주기, 편집, 순서 변경 및 삭제를 바로 사용할 수 있습니다. 양식 스위치는 꺼짐일 때 회색, 켜짐일 때 파란색이며 체크박스는 선택된 경우에만 표시됩니다.

기본 `0.0.0.0:8789` 리스너는 신뢰할 수 있는 LAN에서 편리하지만, HTTP는 전송 중인 자격 증명이나 프로젝트 데이터를 보호하지 않습니다. 신뢰할 수 없는 네트워크에서는 `127.0.0.1`에 바인딩하거나 HTTPS 리버스 프록시 뒤에 배치하세요. 기본 계정은 없으며 유효한 자격 증명을 설정할 때까지 시작되지 않습니다. 작업 수명 주기, 보안 및 배포에 대해서는 [WebUI 가이드](https://ktoolbox.readthedocs.io/latest/ko/webui/)를 참조하세요.

## 설정

KToolBox는 현재 작업 디렉터리에서 `.env`, 그다음 `prod.env`를 읽습니다. 중첩 필드는 `__`를 사용합니다.

```dotenv
# Pawchive 기본값이며 일반적으로 변경할 필요가 없습니다.
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data

# 다운로드 제어.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY`를 설정하면 파일 다운로드에만 전송됩니다. API 클라이언트는 계정 세션을 전송하지 않습니다.

`.env`는 런타임과 전송 동작을 제어하고, 프로젝트 수준 `ktoolbox.toml`은 크리에이터 목록과 제외 규칙을 저장합니다.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[blockers]]
id = "skip-progress-updates"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["진행 상황 공유"] }] } }
```

설정 참조 생성, 프로젝트 파일 검증 또는 선택적 터미널 편집기 실행:

```bash
ktoolbox config example
ktoolbox config validate
ktoolbox config edit
```

자세한 내용은 [설정 가이드](https://ktoolbox.readthedocs.io/latest/ko/configuration/guide/)와 [`example.env`](example.env)를 참조하세요.

## Python API

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

성공한 호출은 Pydantic v2 모델을 반환합니다. 전송, HTTP 상태, 인증, 찾을 수 없음, 충돌 및 응답 검증 실패에는 각각 다른 예외 클래스가 사용됩니다. [API 문서](https://ktoolbox.readthedocs.io/latest/ko/api/)를 참조하세요.

## v0에서 마이그레이션

v1은 Kemono/Coomer 호환 계층과 이전 `BaseAPI`, 모듈 수준 `get_*`, `APIRet`, 래퍼 응답 인터페이스를 제거했습니다. Fire 명령은 Cyclopts로 대체되었으므로 `download`, `sync`, `creator`, `post`, `config`를 사용하세요. 숨겨진 이전 별칭은 사용 중단 경고와 함께 일시적으로 제공됩니다. `KTOOLBOX_API__SESSION_KEY`를 `KTOOLBOX_DOWNLOADER__SESSION_KEY`로 옮기고 [v1 마이그레이션 가이드](https://ktoolbox.readthedocs.io/latest/ko/migration-v1/)를 확인하세요.

이전 `kemono_openapi.json`은 참고용으로 저장소에 남아 있지만 지원되는 런타임 계약은 아닙니다.

## 개발

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run ruff check k_generator ktoolbox/api ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py tests
poetry run mypy --strict ktoolbox/api/client.py ktoolbox/api/errors.py ktoolbox/api/parameters.py ktoolbox/api/utils.py ktoolbox/blocker ktoolbox/cli.py ktoolbox/cli_app.py ktoolbox/job/stream.py ktoolbox/project_config.py ktoolbox/reporting.py ktoolbox/sync.py
poetry run mkdocs build --strict
cd webui && npm ci && npm run typecheck && npm run lint && npm run test && npm run build && npm run test:e2e
```

기본 테스트는 완전히 오프라인이어야 하며 Pawchive나 다른 원격 서비스에 연결해서는 안 됩니다.

## 라이선스

KToolBox는 [BSD 3-Clause License](LICENSE)에 따라 배포됩니다.
