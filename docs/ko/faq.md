# 자주 묻는 질문

## 계정 즐겨찾기를 사용할 수 없는 이유는 무엇인가요?

KToolBox v1은 로그인이 필요 없는 14개의 Pawchive 작업을 구현합니다. `cookieAuth`로 보호되는 5개의 OpenAPI 작업은 의도적으로 제외하므로 API 클라이언트는 계정 세션을 받거나 전송하지 않습니다.

게시물 신고는 별도의 공개 작업이며 구현되어 있습니다. 성공한 신고는 서버 상태를 변경하고 이미 신고된 게시물은 `PawchiveConflictError`를 반환할 수 있으므로 의도적으로 호출하세요.

## API 호출이 실패하면 어떻게 해야 하나요?

CLI는 부분적으로 파싱한 응답 대신 형식이 지정된 Pawchive 오류를 보고합니다. 일반적인 클래스는 전송, HTTP, 인증, 찾을 수 없음, 충돌 및 응답 검증 오류입니다.

- URL 또는 `service`, 크리에이터 ID, 게시물 ID가 올바른지 확인하세요.
- 연결이 느리면 `KTOOLBOX_API__TIMEOUT`을 늘리세요.
- 일시적 전송, `429`, `5xx` 실패에는 `KTOOLBOX_API__RETRY_TIMES`와 `KTOOLBOX_API__RETRY_INTERVAL`을 조정하세요.
- API 설정에 계정 쿠키를 추가하지 마세요. API 요청은 사용하지 않습니다.

리디렉션, 일반 `4xx` 응답, 충돌 및 잘못된 응답 데이터는 재시도하지 않습니다.

## 파일 다운로드가 403을 반환하는 이유는 무엇인가요?

파일 호스트가 특정 자산에 세션을 요구하면 다운로더 전용 키를 설정하세요.

```dotenv
KTOOLBOX_DOWNLOADER__SESSION_KEY=xxxxx
```

쿠키는 파일 다운로드 요청에만 적용되고 Pawchive API 요청으로 전송되지 않습니다. `.env`와 `prod.env`를 비밀을 포함한 로컬 파일로 취급하고 커밋하지 마세요.

## 중단된 다운로드를 재개하려면 어떻게 하나요?

같은 명령을 다시 실행하세요. KToolBox는 완료된 대상 파일을 건너뜁니다. `downloader.temp_suffix`가 있는 미완료 파일이 있고 서버가 범위를 지원하면 남은 바이트를 요청하고 합친 크기를 검증합니다.

## 표지나 첨부 파일을 비활성화하려면 어떻게 하나요?

```dotenv
# 첨부 파일만.
KTOOLBOX_JOB__DOWNLOAD_FILE=False
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True

# 표지만.
#KTOOLBOX_JOB__DOWNLOAD_FILE=True
#KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`download_file`은 기본 게시물 파일, 일반적으로 표지를 의미합니다. 두 옵션의 기본값은 `True`입니다.

## 첨부 파일을 게시물 디렉터리에 직접 저장할 수 있나요?

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## 긴 파일 이름을 피하려면 어떻게 하나요?

순차 이름이나 형식 정밀도 제한을 사용하세요.

```dotenv
KTOOLBOX_JOB__SEQUENTIAL_FILENAME=True
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{id}_{title:.30}
KTOOLBOX_JOB__FILENAME_FORMAT={title:.30}_{}
```

## 프록시를 설정하려면 어떻게 하나요?

HTTPX는 표준 프록시 환경 변수를 읽습니다.

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=socks5://127.0.0.1:7897
```

PowerShell에서는:

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
```

## 설정 편집기가 열리지 않는 이유는 무엇인가요?

선택적 터미널 UI 종속성을 설치하세요.

```bash
pip install "ktoolbox[urwid]"
# 또는
pipx install "ktoolbox[urwid]" --force
```

## 여러 크리에이터를 정기적으로 동기화하려면 어떻게 하나요?

각 크리에이터를 프로젝트 목록에 추가하고 선택적으로 짧은 별칭을 지정한 다음 대상 없는 `sync`를 실행하세요.

```bash
ktoolbox creator add fanbox:123 --alias studio-a
ktoolbox creator add patreon:456 --alias studio-b
ktoolbox sync
```

`creator disable`로 항목을 유지하면서 대상 없는 실행에서 제외할 수 있습니다. 비활성 별칭도 명시적으로 동기화할 수 있습니다. 크리에이터 준비와 파일 전송은 동시성 제한이 분리되어 있어 큰 크리에이터가 준비된 다운로드를 독점하지 않습니다.

## 크리에이터마다 다른 주제를 제외하려면 어떻게 하나요?

`ktoolbox.toml`에 별도의 `[[blockers]]` 항목을 추가하세요. 모두가 공유하는 규칙에는 `scope.mode = "global"`, 선택한 크리에이터에는 정확한 `service:id`와 함께 `scope.mode = "creators"`를 사용하세요. 파일 순서로 평가하고 첫 일치에서 중단합니다.

긴 실행 전에 정규식과 범위를 검증하세요.

```bash
ktoolbox config validate
```

## 리디렉션된 로그에서 진행률이 다르게 보이는 이유는 무엇인가요?

Rich 실시간 진행률은 대화형 터미널에서만 사용됩니다. 각 활성 파일의 속도와 ETA, `Files` 행에 모든 활성 다운로드의 합계 속도를 표시합니다. 파이프, CI, `NO_COLOR`, `--plain`은 로그가 ANSI 실시간 영역을 손상하지 않도록 안정적인 줄 출력을 사용합니다. 색상 없는 대화형 레이아웃에는 `--no-color`, 진행률과 일반 로그를 숨기려면 `--quiet`를 사용하세요.

## WebUI가 시작을 거부하는 이유는 무엇인가요?

`ktoolbox[webui]`를 설치하고 프로젝트 디렉터리를 전달하세요. 계정 설정은 선택 사항이며 없으면 이번 실행용 `admin`과 무작위 암호가 터미널에 출력됩니다. 명시한 해시는 유효한 Argon2 값이어야 합니다. `ktoolbox.toml`은 경고 후 생성되고 프로젝트 잠금은 같은 프로젝트의 두 번째 프로세스를 계속 거부합니다.

## 네트워크에 WebUI를 노출해도 안전한가요?

기본 서버는 일반 HTTP이므로 신뢰할 수 있는 LAN에서만 `0.0.0.0`을 사용하세요. 로컬에서는 `127.0.0.1`에 바인딩하고 원격에서는 HTTPS 리버스 프록시 뒤에 배치하세요. 인증, CSRF, 엄격한 쿠키, 속도 제한, 보안 헤더가 애플리케이션을 보호하지만 HTTP 경로를 암호화할 수는 없습니다.

## 재시작 후 WebUI 작업은 어떻게 되나요?

대기 중인 작업은 그대로 대기합니다. 실행 중이던 작업은 설정과 원격 상태가 바뀌었을 수 있어 자동으로 다시 시작하지 않고 `interrupted`로 표시됩니다. 검토한 후 수동으로 재개하세요. 완료된 파일과 재개 가능한 임시 파일은 유지됩니다.

## WebUI 작업을 삭제하면 관련 없는 파일도 삭제되나요?

일반 삭제는 작업 기록만 제거합니다. 출력 삭제는 미리 보기와 확인 후 작업의 산출물 소유권 기록과 파일 메타데이터를 검사합니다. 기존, 수정, 공유, 일반 파일이 아닌 경로 및 심볼릭 링크를 건너뜁니다.

## uvloop 또는 winloop가 필요한가요?

아니요. 선택적 이벤트 루프 최적화입니다. Linux/macOS에서는 `ktoolbox[uvloop]`, Windows에서는 `ktoolbox[winloop]`를 사용하세요. 둘 다 없으면 표준 asyncio 루프로 계속 실행합니다.

## 바이러스 백신이 패키지 실행 파일을 표시하는 이유는 무엇인가요?

일부 휴리스틱 스캐너는 PyInstaller 번들이나 다운로드 관리자를 표시합니다. 릴리스는 저장소의 공개 자동화로 빌드됩니다. `pipx`로 설치하거나 소스를 감사하고 로컬에서 빌드할 수도 있습니다.
