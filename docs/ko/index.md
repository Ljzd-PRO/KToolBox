# KToolBox

KToolBox는 공개 [Pawchive](https://pawchive.pw/) 데이터를 위한 비동기 명령줄 다운로더, HeroUI 프로젝트 패널 및 형식 지정 Python 클라이언트입니다. 버전 1은 Pawchive만 지원하며 Python 3.10~3.14가 필요합니다.

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

## 다음 단계

- [명령 가이드](commands/guide.md)
- [WebUI 가이드](webui.md)
- [설정 가이드](configuration/guide.md)
- [Python API](api.md)
- [v1로 마이그레이션](migration-v1.md)
- [자주 묻는 질문](faq.md)
