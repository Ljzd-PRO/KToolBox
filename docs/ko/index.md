# KToolBox 시작하기

KToolBox는 Pawchive의 공개 작품을 다운로드합니다. 권장 사용 방법은 WebUI입니다. 일반 작업을 안내 양식으로 수행하며 다른 페이지로 이동한 뒤에도 진행률을 확인할 수 있습니다.

!!! warning "새 메이저 버전"
    v1은 실제 환경 검증이 아직 충분하지 않아 일부 기능이 실패할 수 있습니다. 마이그레이션 전에 기존 설정과 다운로드를 백업하고 예상하지 못한 동작을 알려 주세요.

## WebUI로 시작하기

1. WebUI 패키지를 설치합니다.
2. 동기화 프로젝트용 디렉터리를 만듭니다.
3. 해당 디렉터리에서 KToolBox를 시작합니다.

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

브라우저가 자동으로 열립니다. 터미널에 표시된 `admin`과 무작위 비밀번호로 로그인하고 크리에이터를 추가한 뒤 첫 작업을 만드세요. 필요하면 KToolBox가 `ktoolbox.toml`을 만들며 기본 출력 위치는 `downloads`입니다.

![KToolBox WebUI 개요](../assets/webui/40-overview-showcase-desktop-light.png)

## 다음 단계 선택

<div class="grid cards" markdown>

-   :material-account-multiple-plus-outline: **크리에이터 추가 및 다운로드**

    [프로젝트 작업 흐름](webui/project-workflows.md)에 따라 크리에이터를 추가하고 작품을 검색하며 작업과 제외 규칙을 설정합니다.

-   :material-progress-download: **작업 확인**

    [작업과 실시간 업데이트](webui/tasks.md)에서 진행률, 재시도, 일시 중지, 중지, 재실행 및 안전한 정리를 확인합니다.

-   :material-calendar-sync-outline: **일정에 따라 실행**

    [자동 동기화 가이드](automatic-sync.md)에서 반복 계획을 만듭니다.

-   :material-folder-cog-outline: **이름과 폴더 설정**

    [이름 형식 가이드](naming.md)에서 기본 출력 위치와 읽기 쉬운 구조를 설정합니다.

</div>

## 고급 경로

일반적인 첫 실행에는 아래 페이지가 필요하지 않습니다.

| 목표 | 가이드 |
| --- | --- |
| 고정 로그인 또는 다른 컴퓨터에 배포 | [WebUI 배포 참고](webui/reference.md) |
| 터미널 자동화 | [CLI 가이드](commands/guide.md)와 [명령 참고](commands/reference.md) |
| 모든 설정 확인 | [설정 가이드](configuration/guide.md)와 [참고](configuration/reference.md) |
| AI 클라이언트 또는 Python 프로그램 연결 | [MCP](mcp.md)와 [Python API](api.md) |
| 기존 프로젝트 업그레이드 또는 문제 해결 | [마이그레이션 가이드](migration-v1.md)와 [FAQ](faq.md) |

## 안전한 기본값

WebUI는 로그인 정보를 생성하고 민감한 미디어 미리 보기를 끄며 프로젝트 내부 출력 디렉터리를 사용합니다. 이 컴퓨터에서만 사용할 때는 `127.0.0.1`에 바인딩하고 신뢰할 수 없는 네트워크에서는 HTTPS를 사용하세요. KToolBox는 Pawchive 계정 또는 즐겨찾기 작업을 구현하지 않습니다.
