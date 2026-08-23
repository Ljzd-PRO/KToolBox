# KToolBox

KToolBox는 공개 [Pawchive](https://pawchive.pw/) 데이터를 위한 비동기 명령줄 다운로더, HeroUI 프로젝트 패널 및 형식 지정 Python 클라이언트입니다. 버전 1은 Pawchive만 지원하며 Python 3.10~3.14가 필요합니다.

!!! warning "v1은 새로운 주요 버전입니다"
    이 릴리스 계열은 아직 충분한 실제 사용 검증을 받지 못했습니다. 먼저 범위를 제한한 다운로드를 실행하고 기존 설정을 백업한 뒤 예상하지 못한 동작을 보고해 주세요. Kemono를 더 이상 사용할 수 없으므로 KToolBox는 기본적으로 Pawchive 미러를 사용합니다.

## 사용 경로 선택

<div class="grid cards" markdown>

-   :material-console-line: **명령줄로 시작**

    KToolBox를 설치하고 범위를 제한한 다운로드를 한 번 실행한 다음 [명령 가이드](commands/guide.md)를 읽습니다.

-   :material-view-dashboard-outline: **브라우저에서 프로젝트 관리**

    선택적 패널을 설치하고 [WebUI 가이드](webui.md)에 따라 로그인, 보안, 작업 및 프로젝트 설정을 확인합니다.

-   :material-update: **v0에서 업그레이드**

    이전 dotenv 파일을 백업하고 기존 다운로드를 변경하기 전에 [v1 마이그레이션](migration-v1.md)을 따릅니다.

-   :material-calendar-sync: **크리에이터를 정기적으로 업데이트**

    먼저 목록을 구성한 다음 [자동 동기화](automatic-sync.md)로 정기 확인을 설정합니다.

</div>

## 주요 기능

- 게시물 하나를 다운로드하거나 크리에이터 목록을 동시에 동기화합니다.
- 다운로드 작업을 만들기 전에 순서가 있는 전역 또는 크리에이터 범위 제외 규칙을 적용합니다.
- 부분 파일을 재개하고 기존 파일을 건너뜁니다.
- 날짜, 제목, 파일 이름 패턴 및 파일 크기로 필터링합니다.
- 표지, 첨부 파일, 본문 이미지, 메타데이터 및 외부 링크 출력을 개별 제어합니다.
- 프로젝트 설정, 크리에이터 목록 및 제외 규칙 편집, Pawchive 쿼리, 작업 수명 주기 제어를 위한 7개 언어의 영구 WebUI를 제공합니다.
- 검증된 Pydantic 모델을 통해 Pawchive OpenAPI의 14개 공개 작업을 모두 제공합니다.

계정 인증이 필요한 즐겨찾기 작업은 의도적으로 구현하지 않았습니다. 다운로더 세션 키를 설정한 경우 파일 호스트에만 전송됩니다.

## 설치

`pipx`를 사용하면 애플리케이션을 격리할 수 있습니다.

```bash
pipx install ktoolbox
```

선택적 터미널 편집기와 최적화된 이벤트 루프 지원 설치:

```bash
# Linux / macOS
pipx install "ktoolbox[urwid,uvloop]" --force

# Windows
pipx install "ktoolbox[urwid,winloop]" --force
```

필요할 때 브라우저 패널을 별도로 설치합니다.

```bash
pipx install "ktoolbox[webui]" --force
```

## 빠른 시작

```bash
# 명령과 옵션을 확인합니다.
ktoolbox -h
ktoolbox download -h

# 게시물 하나를 다운로드합니다.
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570

# 더 넓은 범위를 동기화하기 전에 게시물 하나부터 시작합니다.
ktoolbox sync https://pawchive.pw/fanbox/user/6570768 --length 1
```

![KToolBox 명령 개요](../assets/cli-overview.png)

여러 크리에이터를 저장하고 활성화된 항목을 모두 동기화합니다.

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

다시 실행하면 기존 파일을 건너뜁니다. 파일 서버가 바이트 범위를 지원하면 설정된 임시 접미사가 있는 미완료 파일을 재개합니다.

`--output`을 지정하지 않으면 프로젝트 기본 위치를 사용합니다. 설정을 변경하지 않았다면 프로젝트 아래의 `downloads`입니다.

## 문서 지도

| 목표 | 읽을 문서 |
| --- | --- |
| 일상 명령 배우기 | [명령 가이드](commands/guide.md)와 [명령 참조](commands/reference.md) |
| 브라우저 패널 실행 | [WebUI 가이드](webui.md) |
| 정기 확인 예약 | [자동 동기화](automatic-sync.md) |
| 디렉터리와 파일 이름 제어 | [이름 형식](naming.md) |
| 모든 설정 이해 | [설정 가이드](configuration/guide.md)와 [설정 참조](configuration/reference.md) |
| 다른 애플리케이션 연결 | [MCP](mcp.md) 또는 [Python API](api.md) |
| 업그레이드 또는 문제 해결 | [v1 마이그레이션](migration-v1.md)과 [자주 묻는 질문](faq.md) |
