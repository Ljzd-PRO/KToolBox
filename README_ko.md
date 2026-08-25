<div align="center">

# KToolBox

[Pawchive](https://pawchive.pw/) 공개 작품을 다운로드하는 사용하기 쉬운 WebUI, CLI 및 Python 클라이언트입니다.

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/ko/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1은 새로운 메이저 버전이며 실제 환경 검증이 아직 충분하지 않습니다. 일부 기능이 실패할 수 있으니 문제가 있으면 알려 주세요.
>
> Kemono를 더 이상 사용할 수 없어 KToolBox는 기본적으로 미러 사이트 Pawchive를 사용합니다.

## WebUI로 시작하기

WebUI는 KToolBox의 권장 사용 방법입니다. 명령이나 설정 파일을 먼저 배우지 않고 작품 다운로드, 크리에이터 동기화, 자동 동기화, 이름 지정, 필터, 진행률 및 프로젝트 설정을 관리할 수 있습니다.

1. WebUI와 함께 KToolBox를 설치합니다.

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. 프로젝트 디렉터리를 만들고 시작합니다.

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. 브라우저가 자동으로 열립니다. 터미널에 표시된 사용자 이름과 무작위 비밀번호로 로그인합니다.
4. **크리에이터**에서 대상을 추가한 뒤 **작업**에서 동기화 또는 다운로드 작업을 만듭니다.

`ktoolbox.toml`이 없으면 자동으로 생성하며 기본 다운로드 위치는 프로젝트의 `downloads` 디렉터리입니다.

![KToolBox WebUI 개요](docs/assets/webui/40-overview-showcase-desktop-light.png)

짧은 [WebUI 가이드](https://ktoolbox.readthedocs.io/latest/ko/webui/)를 계속 읽거나 [문서 홈](https://ktoolbox.readthedocs.io/latest/ko/)에서 원하는 작업을 선택하세요.

## WebUI에서 할 수 있는 일

- 단일 작품 다운로드와 여러 크리에이터 병렬 동기화.
- 크리에이터 목록, 제외 규칙, 이름 형식 및 여러 자동 동기화 계획 관리.
- 영구 작업 기록, 실시간 진행률, 총속도, 재시도, 일시 중지, 중지, 재실행 및 안전한 정리.
- 설명이 있는 양식과 필요한 위치의 경로 선택기로 프로젝트 설정 관리.
- 7개 언어, 반응형 레이아웃, 밝고 어두운 테마 및 선택적 NSFW 미디어 미리 보기.
- Codex, Claude, Cursor, VS Code 등에 연결하는 내장 MCP 서비스.

## 선택 설정

첫 실행에는 자동 생성 로그인으로 충분합니다. 고정 비밀번호가 필요하면 해시를 생성하여 프로젝트 `.env`에 추가하세요.

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

이 컴퓨터에서만 사용할 때는 `--host 127.0.0.1`을 지정할 수 있습니다. 내장 서버는 HTTP를 사용하므로 원격 접근에는 신뢰할 수 있는 네트워크 또는 HTTPS 리버스 프록시를 사용하세요.

## 고급 사용

스크립트와 터미널 작업에는 CLI도 사용할 수 있습니다.

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

명령은 [CLI 가이드](https://ktoolbox.readthedocs.io/latest/ko/commands/guide/), AI 클라이언트는 [MCP 가이드](https://ktoolbox.readthedocs.io/latest/ko/mcp/), 프로그램 통합은 [Python API](https://ktoolbox.readthedocs.io/latest/ko/api/)를 참고하세요.

## v0에서 업그레이드

업그레이드 전에 `.env`, `prod.env` 및 기존 다운로드를 백업하세요. WebUI는 이전 이름 설정을 감지하고 설정과 디렉터리 변환을 안내합니다. 기존 프로젝트를 변경하기 전에 [v1 마이그레이션 가이드](https://ktoolbox.readthedocs.io/latest/ko/migration-v1/)를 읽고, 실패하면 [문제 해결](https://ktoolbox.readthedocs.io/latest/ko/faq/)을 확인하세요.

## 개발

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

기본 테스트는 완전히 오프라인이며 Pawchive나 다른 원격 서비스에 접속하면 안 됩니다.

## 라이선스

KToolBox는 [BSD 3-Clause License](LICENSE)로 배포됩니다.
