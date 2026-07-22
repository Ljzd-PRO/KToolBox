from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ktoolbox" / "webui" / "config_locale_catalogs.py"
LOCALES = ("zh-Hant", "ja", "ko", "fr", "ru")
MODEL_SECTIONS = {"api", "downloader", "job.post_structure", "job", "webui", "logger"}

SECTION_LABELS = {
    "zh-Hant": {"api": "Pawchive API", "downloader": "檔案下載", "job": "下載工作", "logger": "日誌", "webui": "WebUI", "general": "一般"},
    "ja": {"api": "Pawchive API", "downloader": "ファイルダウンロード", "job": "ダウンロードジョブ", "logger": "ログ", "webui": "WebUI", "general": "一般"},
    "ko": {"api": "Pawchive API", "downloader": "파일 다운로드", "job": "다운로드 작업", "logger": "로그", "webui": "WebUI", "general": "일반"},
    "fr": {"api": "API Pawchive", "downloader": "Téléchargements", "job": "Tâches de téléchargement", "logger": "Journalisation", "webui": "WebUI", "general": "Général"},
    "ru": {"api": "API Pawchive", "downloader": "Загрузка файлов", "job": "Задачи загрузки", "logger": "Журналирование", "webui": "WebUI", "general": "Общие"},
}

LABELS = {
    "zh-Hant": {
        "api.scheme": "API 通訊協定", "api.netloc": "API 主機", "api.statics_netloc": "靜態資源主機", "api.path": "API 根路徑", "api.timeout": "API 逾時時間", "api.retry_times": "API 重試次數", "api.retry_interval": "API 重試間隔",
        "downloader.scheme": "檔案通訊協定", "downloader.files_netloc": "檔案主機", "downloader.file_path_prefix": "檔案路徑前綴", "downloader.session_key": "檔案工作階段金鑰", "downloader.timeout": "下載逾時時間", "downloader.encoding": "文字編碼", "downloader.buffer_size": "檔案緩衝區大小", "downloader.chunk_size": "下載區塊大小", "downloader.temp_suffix": "暫存檔副檔名", "downloader.retry_times": "下載重試次數", "downloader.retry_stop_never": "無限重試", "downloader.retry_interval": "下載重試間隔", "downloader.tps_limit": "每秒連線數", "downloader.use_bucket": "儲存桶模式", "downloader.bucket_path": "儲存桶路徑", "downloader.reverse_proxy": "下載反向代理", "downloader.keep_metadata": "保留檔案詮釋資料",
        "job.count": "同時下載數", "job.creator_concurrency": "同時處理作者數", "job.include_revisions": "包含修訂版本", "job.post_dirname_format": "作品目錄格式", "job.post_structure.attachments": "附件目錄", "job.post_structure.content": "正文檔案", "job.post_structure.external_links": "外部連結檔案", "job.post_structure.file": "主要檔案名稱格式", "job.post_structure.revisions": "修訂目錄", "job.mix_posts": "混合作品檔案", "job.sequential_filename": "循序檔案名稱", "job.sequential_filename_excludes": "循序命名排除項目", "job.filename_format": "附件檔案名稱格式", "job.allow_list": "允許的檔案模式", "job.block_list": "排除的檔案模式", "job.extract_content": "儲存作品正文", "job.extract_content_images": "下載正文圖片", "job.extract_external_links": "儲存外部連結", "job.external_link_patterns": "外部連結模式", "job.group_by_year": "依年份分組", "job.group_by_month": "依月份分組", "job.year_dirname_format": "年份目錄格式", "job.month_dirname_format": "月份目錄格式", "job.keywords": "標題必要關鍵字", "job.keywords_exclude": "舊版排除關鍵字", "job.download_file": "下載主要檔案", "job.download_attachments": "下載附件", "job.min_file_size": "最小檔案大小", "job.max_file_size": "最大檔案大小",
        "logger.path": "日誌目錄", "logger.level": "日誌層級", "logger.rotation": "日誌輪替",
        "webui.host": "WebUI 監聽位址", "webui.port": "WebUI 連接埠", "webui.open_browser": "啟動時開啟瀏覽器", "webui.username": "WebUI 使用者名稱", "webui.password_hash": "WebUI 密碼雜湊", "webui.password": "WebUI 純文字密碼", "webui.max_active_tasks": "執行中工作上限", "webui.session_idle_hours": "工作階段閒置期限", "webui.session_absolute_hours": "工作階段最長期限",
        "ssl_verify": "驗證 TLS 憑證", "json_dump_indent": "JSON 縮排", "use_uvloop": "使用最佳化事件迴圈",
    },
    "ja": {
        "api.scheme": "APIプロトコル", "api.netloc": "APIホスト", "api.statics_netloc": "静的アセットホスト", "api.path": "APIルートパス", "api.timeout": "APIタイムアウト", "api.retry_times": "API再試行回数", "api.retry_interval": "API再試行間隔",
        "downloader.scheme": "ファイルプロトコル", "downloader.files_netloc": "ファイルホスト", "downloader.file_path_prefix": "ファイルパスの接頭辞", "downloader.session_key": "ファイル用セッションキー", "downloader.timeout": "ダウンロードタイムアウト", "downloader.encoding": "テキストエンコーディング", "downloader.buffer_size": "ファイルバッファーサイズ", "downloader.chunk_size": "ダウンロードチャンクサイズ", "downloader.temp_suffix": "一時ファイル接尾辞", "downloader.retry_times": "ダウンロード再試行回数", "downloader.retry_stop_never": "無制限に再試行", "downloader.retry_interval": "ダウンロード再試行間隔", "downloader.tps_limit": "1秒あたりの接続数", "downloader.use_bucket": "ストレージバケットモード", "downloader.bucket_path": "ストレージバケットのパス", "downloader.reverse_proxy": "ダウンロード用リバースプロキシ", "downloader.keep_metadata": "ファイルメタデータを保持",
        "job.count": "同時ダウンロード数", "job.creator_concurrency": "同時クリエイター数", "job.include_revisions": "リビジョンを含める", "job.post_dirname_format": "作品ディレクトリ形式", "job.post_structure.attachments": "添付ファイルディレクトリ", "job.post_structure.content": "本文ファイル", "job.post_structure.external_links": "外部リンクファイル", "job.post_structure.file": "メインファイル名形式", "job.post_structure.revisions": "リビジョンディレクトリ", "job.mix_posts": "作品ファイルを混在", "job.sequential_filename": "連番ファイル名", "job.sequential_filename_excludes": "連番命名の除外対象", "job.filename_format": "添付ファイル名形式", "job.allow_list": "許可するファイルパターン", "job.block_list": "除外するファイルパターン", "job.extract_content": "作品本文を保存", "job.extract_content_images": "本文画像をダウンロード", "job.extract_external_links": "外部リンクを保存", "job.external_link_patterns": "外部リンクパターン", "job.group_by_year": "年ごとに分類", "job.group_by_month": "月ごとに分類", "job.year_dirname_format": "年ディレクトリ形式", "job.month_dirname_format": "月ディレクトリ形式", "job.keywords": "必須タイトルキーワード", "job.keywords_exclude": "旧式の除外キーワード", "job.download_file": "メインファイルをダウンロード", "job.download_attachments": "添付ファイルをダウンロード", "job.min_file_size": "最小ファイルサイズ", "job.max_file_size": "最大ファイルサイズ",
        "logger.path": "ログディレクトリ", "logger.level": "ログレベル", "logger.rotation": "ログローテーション",
        "webui.host": "WebUI待受アドレス", "webui.port": "WebUIポート", "webui.open_browser": "起動時にブラウザーを開く", "webui.username": "WebUIユーザー名", "webui.password_hash": "WebUIパスワードハッシュ", "webui.password": "WebUI平文パスワード", "webui.max_active_tasks": "実行中タスクの上限", "webui.session_idle_hours": "セッションのアイドル期限", "webui.session_absolute_hours": "セッションの最長期限",
        "ssl_verify": "TLS証明書を検証", "json_dump_indent": "JSONインデント", "use_uvloop": "最適化イベントループを使用",
    },
    "ko": {
        "api.scheme": "API 프로토콜", "api.netloc": "API 호스트", "api.statics_netloc": "정적 자산 호스트", "api.path": "API 루트 경로", "api.timeout": "API 시간 제한", "api.retry_times": "API 재시도 횟수", "api.retry_interval": "API 재시도 간격",
        "downloader.scheme": "파일 프로토콜", "downloader.files_netloc": "파일 호스트", "downloader.file_path_prefix": "파일 경로 접두사", "downloader.session_key": "파일 세션 키", "downloader.timeout": "다운로드 시간 제한", "downloader.encoding": "텍스트 인코딩", "downloader.buffer_size": "파일 버퍼 크기", "downloader.chunk_size": "다운로드 청크 크기", "downloader.temp_suffix": "임시 파일 접미사", "downloader.retry_times": "다운로드 재시도 횟수", "downloader.retry_stop_never": "무제한 재시도", "downloader.retry_interval": "다운로드 재시도 간격", "downloader.tps_limit": "초당 연결 수", "downloader.use_bucket": "스토리지 버킷 모드", "downloader.bucket_path": "스토리지 버킷 경로", "downloader.reverse_proxy": "다운로드 리버스 프록시", "downloader.keep_metadata": "파일 메타데이터 유지",
        "job.count": "동시 다운로드 수", "job.creator_concurrency": "동시 크리에이터 수", "job.include_revisions": "리비전 포함", "job.post_dirname_format": "작품 디렉터리 형식", "job.post_structure.attachments": "첨부 파일 디렉터리", "job.post_structure.content": "본문 파일", "job.post_structure.external_links": "외부 링크 파일", "job.post_structure.file": "기본 파일 이름 형식", "job.post_structure.revisions": "리비전 디렉터리", "job.mix_posts": "작품 파일 혼합", "job.sequential_filename": "순차 파일 이름", "job.sequential_filename_excludes": "순차 이름 제외 항목", "job.filename_format": "첨부 파일 이름 형식", "job.allow_list": "허용할 파일 패턴", "job.block_list": "제외할 파일 패턴", "job.extract_content": "작품 본문 저장", "job.extract_content_images": "본문 이미지 다운로드", "job.extract_external_links": "외부 링크 저장", "job.external_link_patterns": "외부 링크 패턴", "job.group_by_year": "연도별 분류", "job.group_by_month": "월별 분류", "job.year_dirname_format": "연도 디렉터리 형식", "job.month_dirname_format": "월 디렉터리 형식", "job.keywords": "필수 제목 키워드", "job.keywords_exclude": "이전 제외 키워드", "job.download_file": "기본 파일 다운로드", "job.download_attachments": "첨부 파일 다운로드", "job.min_file_size": "최소 파일 크기", "job.max_file_size": "최대 파일 크기",
        "logger.path": "로그 디렉터리", "logger.level": "로그 수준", "logger.rotation": "로그 순환",
        "webui.host": "WebUI 수신 주소", "webui.port": "WebUI 포트", "webui.open_browser": "시작할 때 브라우저 열기", "webui.username": "WebUI 사용자 이름", "webui.password_hash": "WebUI 비밀번호 해시", "webui.password": "WebUI 평문 비밀번호", "webui.max_active_tasks": "활성 작업 한도", "webui.session_idle_hours": "세션 유휴 기한", "webui.session_absolute_hours": "최대 세션 기한",
        "ssl_verify": "TLS 인증서 검증", "json_dump_indent": "JSON 들여쓰기", "use_uvloop": "최적화 이벤트 루프 사용",
    },
    "fr": {
        "api.scheme": "Protocole de l’API", "api.netloc": "Hôte de l’API", "api.statics_netloc": "Hôte des ressources statiques", "api.path": "Chemin racine de l’API", "api.timeout": "Délai de l’API", "api.retry_times": "Tentatives de l’API", "api.retry_interval": "Intervalle des tentatives de l’API",
        "downloader.scheme": "Protocole des fichiers", "downloader.files_netloc": "Hôte des fichiers", "downloader.file_path_prefix": "Préfixe du chemin des fichiers", "downloader.session_key": "Clé de session des fichiers", "downloader.timeout": "Délai de téléchargement", "downloader.encoding": "Encodage du texte", "downloader.buffer_size": "Taille du tampon de fichier", "downloader.chunk_size": "Taille des blocs téléchargés", "downloader.temp_suffix": "Suffixe temporaire", "downloader.retry_times": "Tentatives de téléchargement", "downloader.retry_stop_never": "Réessayer sans limite", "downloader.retry_interval": "Intervalle des tentatives", "downloader.tps_limit": "Connexions par seconde", "downloader.use_bucket": "Mode de stockage local", "downloader.bucket_path": "Chemin du stockage local", "downloader.reverse_proxy": "Proxy inverse de téléchargement", "downloader.keep_metadata": "Conserver les métadonnées des fichiers",
        "job.count": "Téléchargements simultanés", "job.creator_concurrency": "Créateurs simultanés", "job.include_revisions": "Inclure les révisions", "job.post_dirname_format": "Format du répertoire d’une œuvre", "job.post_structure.attachments": "Répertoire des pièces jointes", "job.post_structure.content": "Fichier du contenu", "job.post_structure.external_links": "Fichier des liens externes", "job.post_structure.file": "Format du fichier principal", "job.post_structure.revisions": "Répertoire des révisions", "job.mix_posts": "Mélanger les fichiers des œuvres", "job.sequential_filename": "Noms de fichiers séquentiels", "job.sequential_filename_excludes": "Exclusions des noms séquentiels", "job.filename_format": "Format des pièces jointes", "job.allow_list": "Motifs de fichiers autorisés", "job.block_list": "Motifs de fichiers exclus", "job.extract_content": "Enregistrer le contenu de l’œuvre", "job.extract_content_images": "Télécharger les images du contenu", "job.extract_external_links": "Enregistrer les liens externes", "job.external_link_patterns": "Motifs de liens externes", "job.group_by_year": "Regrouper par année", "job.group_by_month": "Regrouper par mois", "job.year_dirname_format": "Format du répertoire d’année", "job.month_dirname_format": "Format du répertoire de mois", "job.keywords": "Mots-clés requis dans le titre", "job.keywords_exclude": "Anciens mots-clés d’exclusion", "job.download_file": "Télécharger le fichier principal", "job.download_attachments": "Télécharger les pièces jointes", "job.min_file_size": "Taille minimale des fichiers", "job.max_file_size": "Taille maximale des fichiers",
        "logger.path": "Répertoire des journaux", "logger.level": "Niveau des journaux", "logger.rotation": "Rotation des journaux",
        "webui.host": "Adresse d’écoute de la WebUI", "webui.port": "Port de la WebUI", "webui.open_browser": "Ouvrir le navigateur au démarrage", "webui.username": "Nom d’utilisateur de la WebUI", "webui.password_hash": "Hachage du mot de passe WebUI", "webui.password": "Mot de passe WebUI en clair", "webui.max_active_tasks": "Limite des tâches actives", "webui.session_idle_hours": "Durée d’inactivité de session", "webui.session_absolute_hours": "Durée maximale de session",
        "ssl_verify": "Vérifier les certificats TLS", "json_dump_indent": "Indentation JSON", "use_uvloop": "Utiliser la boucle d’événements optimisée",
    },
    "ru": {
        "api.scheme": "Протокол API", "api.netloc": "Хост API", "api.statics_netloc": "Хост статических ресурсов", "api.path": "Корневой путь API", "api.timeout": "Тайм-аут API", "api.retry_times": "Число попыток API", "api.retry_interval": "Интервал попыток API",
        "downloader.scheme": "Протокол файлов", "downloader.files_netloc": "Файловый хост", "downloader.file_path_prefix": "Префикс пути файлов", "downloader.session_key": "Ключ сеанса файлов", "downloader.timeout": "Тайм-аут загрузки", "downloader.encoding": "Кодировка текста", "downloader.buffer_size": "Размер файлового буфера", "downloader.chunk_size": "Размер блока загрузки", "downloader.temp_suffix": "Суффикс временных файлов", "downloader.retry_times": "Число попыток загрузки", "downloader.retry_stop_never": "Повторять без ограничений", "downloader.retry_interval": "Интервал попыток загрузки", "downloader.tps_limit": "Соединений в секунду", "downloader.use_bucket": "Режим локального хранилища", "downloader.bucket_path": "Путь локального хранилища", "downloader.reverse_proxy": "Обратный прокси загрузки", "downloader.keep_metadata": "Сохранять метаданные файлов",
        "job.count": "Параллельные загрузки", "job.creator_concurrency": "Параллельные авторы", "job.include_revisions": "Включать ревизии", "job.post_dirname_format": "Формат каталога работы", "job.post_structure.attachments": "Каталог вложений", "job.post_structure.content": "Файл содержимого", "job.post_structure.external_links": "Файл внешних ссылок", "job.post_structure.file": "Формат основного файла", "job.post_structure.revisions": "Каталог ревизий", "job.mix_posts": "Смешивать файлы работ", "job.sequential_filename": "Последовательные имена файлов", "job.sequential_filename_excludes": "Исключения последовательных имён", "job.filename_format": "Формат имени вложений", "job.allow_list": "Разрешённые шаблоны файлов", "job.block_list": "Исключённые шаблоны файлов", "job.extract_content": "Сохранять текст работы", "job.extract_content_images": "Скачивать изображения из текста", "job.extract_external_links": "Сохранять внешние ссылки", "job.external_link_patterns": "Шаблоны внешних ссылок", "job.group_by_year": "Группировать по году", "job.group_by_month": "Группировать по месяцу", "job.year_dirname_format": "Формат каталога года", "job.month_dirname_format": "Формат каталога месяца", "job.keywords": "Обязательные слова заголовка", "job.keywords_exclude": "Устаревшие слова исключения", "job.download_file": "Скачивать основной файл", "job.download_attachments": "Скачивать вложения", "job.min_file_size": "Минимальный размер файла", "job.max_file_size": "Максимальный размер файла",
        "logger.path": "Каталог журналов", "logger.level": "Уровень журналирования", "logger.rotation": "Ротация журналов",
        "webui.host": "Адрес прослушивания WebUI", "webui.port": "Порт WebUI", "webui.open_browser": "Открывать браузер при запуске", "webui.username": "Имя пользователя WebUI", "webui.password_hash": "Хеш пароля WebUI", "webui.password": "Открытый пароль WebUI", "webui.max_active_tasks": "Лимит активных задач", "webui.session_idle_hours": "Срок бездействия сеанса", "webui.session_absolute_hours": "Максимальный срок сеанса",
        "ssl_verify": "Проверять сертификаты TLS", "json_dump_indent": "Отступ JSON", "use_uvloop": "Использовать оптимизированный цикл событий",
    },
}


def _descriptions(locale: str) -> dict[str, str]:
    path = ROOT / "docs" / locale / "configuration" / "reference.md"
    descriptions: dict[str, str] = {}
    section: str | None = ""
    seen_model_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            matches = re.findall(r"`([^`]+)`", line)
            selected = next((value for value in matches if value in MODEL_SECTIONS), None)
            if selected is not None:
                section = selected
                seen_model_section = True
            elif not seen_model_section:
                section = ""
            else:
                section = None
            continue
        if section is None or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not cells[0].startswith("`"):
            continue
        field = cells[0].strip("`")
        path_key = f"{section}.{field}" if section else field
        if path_key in LABELS[locale]:
            descriptions[path_key] = cells[3]
    return descriptions


def render() -> str:
    catalogs = {
        locale: {
            "sections": SECTION_LABELS[locale],
            "labels": LABELS[locale],
            "descriptions": _descriptions(locale),
        }
        for locale in LOCALES
    }
    missing = {
        locale: sorted(set(LABELS[locale]) - set(catalogs[locale]["descriptions"]))
        for locale in LOCALES
    }
    if any(missing.values()):
        raise SystemExit(f"missing translated descriptions: {missing}")
    return (
        "# Generated by scripts/generate_config_locale_catalogs.py; do not edit directly.\n"
        "from __future__ import annotations\n\n"
        f"CONFIG_LOCALE_CATALOGS = {json.dumps(catalogs, ensure_ascii=False, indent=4)}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("configuration locale catalogs are out of date")
        return
    OUTPUT.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
