# WebUI

KToolBox WebUI는 React와 HeroUI로 만든 프로젝트 연결 관리 패널입니다. CLI와 동일한 설정을 편집하고 동일한 Python 서비스를 호출하며 CLI 하위 프로세스를 시작하거나 파싱하지 않습니다. 작업, 시도, 로그 및 소유권 기록은 선택한 프로젝트의 `.ktoolbox/webui.sqlite3`에 영구 저장됩니다.

## 목적에 따라 계속 읽기

<div class="grid cards" markdown>

-   :material-arrow-right-circle-outline: **프로젝트 데이터 관리**

    [프로젝트 작업 흐름](webui/project-workflows.md)에서 크리에이터, 작품, 이름, 설정 및 선택적 미디어를 관리합니다.

-   :material-arrow-right-circle-outline: **다운로드 모니터링**

    [작업과 실시간 업데이트](webui/tasks.md)에서 작업 생성, 진단, 일시 중지, 재개, 재실행 및 안전한 삭제를 수행합니다.

-   :material-arrow-right-circle-outline: **배포와 유지 관리**

    [배포 참고](webui/reference.md)에서 환경 변수, 백업, 실행 환경 및 다국어 범위를 확인합니다.

</div>

## 설치 및 시작

선택적 런타임을 설치하고 프로젝트 디렉터리를 만듭니다.

```bash
pipx install "ktoolbox[webui]" --force
mkdir ktoolbox-project
cd ktoolbox-project
```

시작 시 자격 증명은 선택 사항입니다. 설정하지 않으면 해당 프로세스에서 사용할 `admin`과 새 무작위 암호가 터미널에 출력됩니다. 고정 자격 증명에는 숨겨진 입력으로 Argon2id 해시를 생성하세요.

```bash
ktoolbox webui hash-password
```

계정을 프로젝트의 `.env`에 저장합니다. 셸 스타일 `$` 문자를 그대로 유지하려면 해시를 따옴표로 묶으세요.

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

해당 프로젝트의 패널을 시작합니다.

```bash
ktoolbox webui .
ktoolbox webui . --host 127.0.0.1 --port 8789 --no-open
```

기본값은 `0.0.0.0:8789`이며 로컬 브라우저가 자동으로 열립니다. `--host`, `--port`, `--no-open`은 해당 프로세스의 환경 설정을 재정의합니다. `ktoolbox.toml`이 없으면 경고 후 최소 유효 문서를 원자적으로 만듭니다. 자격 증명이 없어도 시작할 수 있으며 빈 사용자 이름은 `admin`, 두 암호가 모두 비어 있으면 이번 실행용 새 암호를 생성해 터미널에 출력합니다.

## 보안 모델

KToolBox에는 로컬 WebUI 계정 하나만 있습니다. 명시적 설정이 우선하며 `KTOOLBOX_WEBUI__PASSWORD_HASH`는 일반 텍스트 `KTOOLBOX_WEBUI__PASSWORD`보다 우선합니다. 둘 다 없으면 시작할 때마다 메모리에서 암호를 생성하고 유효 사용자 이름과 함께 해당 터미널에만 출력합니다. 안정적 배포에서는 해시를 설정하고 두 dotenv 파일을 버전 관리에서 제외하세요.

세션은 무작위 불투명 토큰을 사용합니다. SQLite에는 토큰 해시만 저장됩니다. 브라우저 쿠키는 `HttpOnly`와 `SameSite=Strict`이고 HTTPS 요청에서는 `Secure`가 됩니다. 상태 변경 요청에는 세션별 CSRF 토큰과 동일 출처 검사가 필요합니다. 로그인 시도는 속도가 제한되고 API 응답은 캐시되지 않으며 엄격한 콘텐츠, 프레임, 리퍼러 및 브라우저 권한 헤더를 전송합니다.

내장 서버는 HTTP를 사용합니다. 기본 LAN 리스너는 신뢰할 수 있는 네트워크에서만 적합하며, 그렇지 않으면 암호, 쿠키, 경로, 로그 및 설정이 전송 중 노출됩니다. 단일 컴퓨터에서는 `--host 127.0.0.1`을 사용하세요. 원격 접근은 신뢰할 수 있는 리버스 프록시에서 HTTPS를 종료하고 네트워크 접근을 제한하세요. 페이지가 안전하지 않은 동안 로그인 페이지와 애플리케이션 셸은 HTTP 경고를 유지합니다.

한 번에 스케줄러 하나만 프로젝트를 열 수 있습니다. 프로젝트 잠금은 두 WebUI 프로세스가 큐와 출력을 두고 경쟁하는 것을 막습니다.
