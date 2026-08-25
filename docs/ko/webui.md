# WebUI

WebUI는 KToolBox의 권장 사용 방법입니다. 한 동기화 프로젝트의 설정, 작업, 진행률 및 기록을 브라우저 화면에서 함께 관리합니다.

## 첫 실행

WebUI 패키지를 설치하고 프로젝트 디렉터리를 만든 뒤 KToolBox를 시작합니다.

```bash
pipx install "ktoolbox[webui]"
mkdir ktoolbox-project
cd ktoolbox-project
ktoolbox webui .
```

브라우저가 자동으로 열립니다. 터미널에 표시된 `admin`과 무작위 비밀번호로 로그인하세요. `ktoolbox.toml`이 없으면 KToolBox가 생성하며 새 작업의 기본 출력은 프로젝트 `downloads`입니다.

![KToolBox WebUI 개요](../assets/webui/40-overview-showcase-desktop-light.png)

## 첫 동기화

1. **크리에이터**를 열고 **크리에이터 추가**를 선택합니다.
2. Pawchive 크리에이터 URL을 붙여 넣거나 플랫폼과 ID를 입력합니다.
3. **작업**을 열고 **작업 만들기**에서 **크리에이터 동기화**를 선택합니다.
4. 새 크리에이터와 이름 형식을 확인하는 동안에는 초기 작품 수를 작게 제한합니다.
5. 작업을 열어 다운로드, 속도, 재시도 및 유용한 활동 메시지를 확인합니다.

완료한 파일은 유지되고 호환되는 임시 파일은 이어받을 수 있습니다. 한 크리에이터가 실패해도 같은 작업에서 성공한 다운로드는 삭제되지 않습니다.

## 목표에 따라 계속하기

<div class="grid cards" markdown>

-   :material-folder-account-outline: **크리에이터, 작품, 제외 및 이름**

    일상적인 프로젝트 관리는 [프로젝트 작업 흐름](webui/project-workflows.md)을 사용하세요.

-   :material-progress-download: **진행률과 작업 제어**

    일시 중지, 중지, 재실행, 진단 및 안전한 정리는 [작업과 실시간 업데이트](webui/tasks.md)를 참고하세요.

-   :material-server-security: **계정과 배포**

    고정 자격 증명, 원격 접근, 백업 또는 상세 보안 동작이 필요할 때만 [배포 참고](webui/reference.md)를 사용하세요.

-   :material-update: **기존 v0 프로젝트**

    이전 설정이나 다운로드를 변환하기 전에 [마이그레이션 가이드](migration-v1.md)를 읽으세요.

</div>

## 선택적 고정 로그인

첫 실행에는 생성된 자격 증명으로 충분합니다. 재시작 후에도 같은 로그인을 유지하려면 비밀번호 해시를 만드세요.

```bash
ktoolbox webui hash-password
```

결과를 프로젝트 `.env`에 추가합니다.

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$v=19$...'
```

## 안전한 접근

내장 서버는 HTTP를 사용합니다. 같은 컴퓨터에서만 사용할 때는 `127.0.0.1`에 바인딩하세요.

```bash
ktoolbox webui . --host 127.0.0.1
```

원격 접근에는 신뢰할 수 있는 네트워크 또는 HTTPS 리버스 프록시를 사용하세요. 로그인할 수 있는 사용자는 프로젝트 경로, 설정 및 작업 로그를 볼 수 있으므로 신뢰할 수 없는 사용자에게 공개하지 마세요. 한 프로젝트는 한 번에 하나의 WebUI 프로세스만 관리할 수 있습니다.
