# 프로젝트 정보

## 개발 브랜치

Pawchive v1 작업은 기본 릴리스 라인이 될 준비가 될 때까지 [`pawchive`](https://github.com/Ljzd-PRO/KToolBox/tree/pawchive) 브랜치에서 관리됩니다.

변경 사항은 계약, 클라이언트, 프로젝트 마이그레이션, 테스트, 문서 및 릴리스 메타데이터를 다루는 집중된 커밋으로 나뉩니다. 정규화된 계약을 기준으로 생성 코드 변경을 감사할 수 있도록 원본 Pawchive OpenAPI 파일은 수정하지 않습니다.

## 품질 정책

기본 테스트 모음은 완전히 오프라인이며 우발적인 네트워크 접근을 차단합니다. 직접 작성한 API 계층은 줄 및 분기 커버리지를 100%로 유지해야 하고, 생성된 모델은 통계에서 제외하며 전체 프로젝트는 85% 이상의 커버리지를 유지해야 합니다.

CI는 지원되는 Python 버전에서 OpenAPI 문서, 결정적 모델 생성, Ruff, API 계층의 엄격한 Mypy, Python 바이트코드 컴파일, 패키지 빌드 및 엄격한 MkDocs 빌드도 검증합니다.

## 라이선스

KToolBox는 [BSD 3-Clause License](https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE)에 따라 배포됩니다.

Copyright © 2023 by Ljzd-PRO.
