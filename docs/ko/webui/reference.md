# WebUI 배포 참고

첫 보안 설정을 마친 뒤 WebUI 인스턴스를 운영하고 백업할 때 이 참고 문서를 사용하세요.

## 정보

정보 페이지는 버전, 라이선스, 실행 환경과 공식 링크를 한곳에 표시합니다. URL, IP 및 수신 주소는 인라인 코드 스타일을 사용합니다.

![어두운 모바일 정보 페이지](../../assets/webui/32-about-mobile-dark.png)

## WebUI 환경 참조

| 변수 | 기본값 | 의미 |
| --- | --- | --- |
| `KTOOLBOX_WEBUI__HOST` | `0.0.0.0` | 수신 인터페이스. |
| `KTOOLBOX_WEBUI__PORT` | `8789` | 1~65535의 수신 포트. |
| `KTOOLBOX_WEBUI__OPEN_BROWSER` | `True` | 시작 후 로컬 URL 열기. |
| `KTOOLBOX_WEBUI__USERNAME` | 비어 있음 → 시작 시 `admin` | 선택적 단일 계정 사용자 이름. |
| `KTOOLBOX_WEBUI__PASSWORD_HASH` | 비어 있음 | 권장 고정 Argon2id 해시. |
| `KTOOLBOX_WEBUI__PASSWORD` | 비어 있음 → 시작마다 무작위 | 일반 텍스트 대체 값. 해시가 있으면 무시. |
| `KTOOLBOX_WEBUI__MAX_ACTIVE_TASKS` | `2` | 동시 최상위 작업, 1~16. |
| `KTOOLBOX_WEBUI__SESSION_IDLE_HOURS` | `24` | 마지막 사용부터의 세션 수명. |
| `KTOOLBOX_WEBUI__SESSION_ABSOLUTE_HOURS` | `168` | 로그인부터의 최대 세션 수명. |

작업 기록이 중요하면 `ktoolbox.toml`, 로컬 dotenv 파일 및 `.ktoolbox/webui.sqlite3`를 함께 백업하세요. WebUI가 실행 중일 때 데이터베이스를 복사하지 마세요.

## 다국어 브라우저 검증

7개 언어 카탈로그를 데스크톱과 모바일의 라이트/다크 테마에서 실제로 검증합니다. 아래는 검증을 통과한 대표 화면이며, 사용자 콘텐츠와 파일 시스템 경로는 원문을 유지합니다.

![프랑스어 모바일 설정 화면](../../assets/webui/24-configuration-mobile-fr.png)

![러시아어 모바일 원격 경로 선택기](../../assets/webui/25-path-picker-mobile-ru.png)

## 관련 WebUI 가이드

- [설치와 보안 개요](../webui.md)
- [프로젝트 작업 흐름](project-workflows.md)
- [작업과 실시간 업데이트](tasks.md)
- [배포 참고](reference.md)
