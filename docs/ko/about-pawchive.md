# Pawchive 소개

[Pawchive](https://pawchive.pw/)는 KToolBox v1이 지원하는 유일한 백엔드입니다. KToolBox는 공개 API를 사용하여 크리에이터와 게시물을 찾은 다음 Pawchive 전용 파일 호스트에서 파일을 다운로드합니다.

## 기본 엔드포인트

| 용도 | 기본값 |
| --- | --- |
| 공개 API | `https://pawchive.pw/api/v1` |
| 크리에이터 아이콘 및 배너 | `https://pawchive.pw` |
| 게시물 파일 | `https://file.pawchive.pw/data/...` |

API 요청은 계정 세션을 전송하지 않습니다. `downloader.session_key`를 설정한 경우 파일 다운로드 요청에만 `session` 쿠키로 전송됩니다.

## 지원하는 API 범위

KToolBox는 공개된 OpenAPI 문서에서 `cookieAuth`가 필요하지 않은 14개 작업을 모두 구현합니다. 여기에는 크리에이터와 게시물 검색, 프로필, 공지, 팬 카드, 링크, 게시물 상세 정보, 파일 해시 검색, 게시물 신고 상태와 제출, 개정판, 댓글 및 애플리케이션 버전이 포함됩니다.

Pawchive 계정 로그인이 필요한 5개의 즐겨찾기 작업은 의도적으로 제외합니다.

## 책임 있는 사용

관련 법률, 플랫폼 약관, 크리에이터 권리 및 저장 공간 제한을 준수하세요. 크리에이터를 처음 테스트할 때는 제한된 동기화(`--length`)와 파일 크기 제한을 사용하세요.
