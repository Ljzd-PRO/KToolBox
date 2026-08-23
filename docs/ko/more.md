# 프로젝트 정보

## 릴리스 상태

KToolBox v1은 Pawchive 기반의 새로운 릴리스 계열입니다. v0과 호환되지 않는 업그레이드이며 아직 충분한 실제 사용 검증을 받지 못했으므로 대규모 동기화에 의존하기 전에 범위를 제한한 다운로드를 시험하세요. 기존 설치를 업데이트할 때는 [v1 마이그레이션](migration-v1.md)부터 시작합니다.

Kemono는 더 이상 사용할 수 없으며 Pawchive만 지원되는 백엔드입니다. 생성 클라이언트 변경을 정규화된 계약과 비교할 수 있도록 원본 Pawchive OpenAPI 파일은 수정하지 않습니다.

## 지원 및 리소스

문서 사이트를 떠나기 전에 사이트 검색과 [자주 묻는 질문](faq.md)을 사용하세요. 답을 찾지 못했다면 목적이 분명한 다음 외부 링크를 이용할 수 있습니다.

- 재현 가능한 결함은 [Issue 추적기](https://github.com/Ljzd-PRO/KToolBox/issues)에 보고합니다.
- 질문과 제안은 [Discussions](https://github.com/Ljzd-PRO/KToolBox/discussions)에 게시합니다.
- 게시된 설명과 결과물은 [Releases](https://github.com/Ljzd-PRO/KToolBox/releases)에서 확인합니다.
- 코드와 기여 기록은 [소스 저장소](https://github.com/Ljzd-PRO/KToolBox)에서 확인합니다.

## 품질 및 라이선스

기본 테스트 모음은 완전히 오프라인이며 우발적인 네트워크 접근을 차단합니다. CI는 OpenAPI 계약, 결정적 생성, 테스트, Ruff, Mypy, Python 바이트코드, 패키지 결과물, WebUI 빌드 및 엄격한 MkDocs 빌드를 검증합니다.

KToolBox는 [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause)에 따라 배포됩니다. Copyright © 2023 by Ljzd-PRO.
