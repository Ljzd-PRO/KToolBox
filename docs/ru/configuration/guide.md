# Руководство по конфигурации

KToolBox использует два уровня конфигурации:

- `.env`, `prod.env` и переменные процесса управляют API, передачей, именованием и глобальным поведением загрузок.
- `ktoolbox.toml` хранит список авторов проекта и упорядоченные правила исключения публикаций.

KToolBox читает `.env`, затем `prod.env` из текущего рабочего каталога. Значения из `prod.env` переопределяют совпадающие значения `.env`, а переменные окружения процесса имеют наивысший приоритет.

Вложенные поля соединяются двойным подчёркиванием. Например, `KTOOLBOX_API__TIMEOUT` соответствует `config.api.timeout`.

```dotenv
# Запросы API Pawchive.
KTOOLBOX_API__TIMEOUT=10
KTOOLBOX_API__RETRY_TIMES=4
KTOOLBOX_API__RETRY_INTERVAL=2

# Передача файлов.
KTOOLBOX_DOWNLOADER__TIMEOUT=30
KTOOLBOX_DOWNLOADER__TPS_LIMIT=5

# Задания на скачивание.
KTOOLBOX_JOB__COUNT=4
KTOOLBOX_JOB__CREATOR_CONCURRENCY=4
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=True
```

Все настройки необязательны. Значения по умолчанию приведены в [справочнике конфигурации](reference.md).

## Создание или изменение конфигурации

Создайте все доступные ключи dotenv из текущей модели:

```bash
ktoolbox config example
```

Необязательный редактор терминала может показывать описания полей, извлечённые из строк документации модели конфигурации:

```bash
pipx install "ktoolbox[urwid]" --force
ktoolbox config edit
```

Необязательная [WebUI](../webui.md) показывает те же описания на английском и упрощённом китайском языках через типизированные элементы управления, индикаторы источника итогового значения, маскирование секретов, редактирование исходного dotenv/TOML, проверку, предварительный просмотр различий и защиту от конфликтов ETag.

Просмотр или проверка файла проекта без открытия редактора:

```bash
ktoolbox config path
ktoolbox config validate
```

Путь проекта разрешается в следующем порядке: глобальный `--config`, `KTOOLBOX_PROJECT_CONFIG`, затем `./ktoolbox.toml`. Для записи используется временный файл в том же каталоге и атомарная замена; TomlKit сохраняет комментарии.

## Список авторов

Каждый проектный документ начинается с `schema_version = 1`. Авторы уникальны по `service:id` без учёта регистра; необязательные псевдонимы также уникальны.

```toml
schema_version = 1

[[creators]]
service = "fanbox"
creator_id = "123"
alias = "studio-a"
enabled = true

[[creators]]
service = "patreon"
creator_id = "456"
alias = "studio-b"
enabled = false
```

Используйте `creator add`, `remove`, `enable` и `disable` вместо ручного изменения простых записей. `sync` без целей использует все включённые записи; явно заданные псевдонимы или идентификаторы выполняются независимо от `enabled`.

## Правила исключения публикаций {#post-blockers}

Правила выполняются в порядке TOML, и первое совпадение исключает публикацию. Глобальное правило применяется ко всем синхронизируемым авторам; область автора перечисляет точные значения `service:id`. Отключённые правила остаются настроенными, но не выполняются.

```toml
[[blockers]]
id = "skip-life-updates"
type = "field-match"
enabled = true
scope = { mode = "global", creators = [] }
options = { rule = { kind = "group", mode = "any", conditions = [{ kind = "field", field = "title", operator = "contains", values = ["life update", "daily note"] }, { kind = "field", field = "tags[*]", operator = "equals", values = ["personal"] }] } }

[[blockers]]
id = "studio-a-progress"
type = "field-match"
enabled = true
scope = { mode = "creators", creators = ["fanbox:123"] }
options = { rule = { kind = "group", mode = "all", conditions = [{ kind = "field", field = "title", operator = "regex", values = ["progress|practice"] }, { kind = "field", field = "attachments[*].name", operator = "exists", expected = false }] } }
```

`field-match` поддерживает рекурсивные группы `any`/`all` и `negate` для группы или условия. Доступные условия:

| Оператор | Поведение |
| --- | --- |
| `contains` | Любое выбранное скалярное значение содержит одно настроенное значение. |
| `equals` | Любое выбранное скалярное значение равно одному настроенному значению. |
| `regex` | Любое выбранное скалярное значение соответствует регулярному выражению. Шаблоны компилируются при проверке конфигурации. |
| `exists` | Выбранный путь существует и не равен null; `expected = false` инвертирует ожидание. |

Сравнения не учитывают регистр, если не задано `case_sensitive = true`. Безопасные точечные пути могут содержать селекторы списков `[*]`, например `tags[*]`, `file.name` и `attachments[*].name`. Отсутствующие пути не совпадают. Выражения Python и произвольный код никогда не вычисляются.

Правила проверяют ответ списка до создания сведений, редакций, каталогов, метаданных или заданий на скачивание. Исключённые публикации и редакции не входят в индекс автора, а совпавший текст не выводится. Асинхронный интерфейс `PostBlocker` и реестр позволяют добавлять будущие типы без изменения координатора синхронизации.

`KTOOLBOX_JOB__KEYWORDS_EXCLUDE` по-прежнему принимается как устаревшее неявное глобальное правило «заголовок содержит». KToolBox не переписывает его автоматически; перенесите его в `ktoolbox.toml`.

## Адреса Pawchive

Стандартные значения v1 обычно не нужно менять:

```dotenv
KTOOLBOX_API__SCHEME=https
KTOOLBOX_API__NETLOC=pawchive.pw
KTOOLBOX_API__STATICS_NETLOC=pawchive.pw
KTOOLBOX_API__PATH=/api/v1
KTOOLBOX_DOWNLOADER__SCHEME=https
KTOOLBOX_DOWNLOADER__FILES_NETLOC=file.pawchive.pw
KTOOLBOX_DOWNLOADER__FILE_PATH_PREFIX=/data
```

`KTOOLBOX_DOWNLOADER__SESSION_KEY` необязателен и прикрепляется только к запросам загрузчика файлов. `PawchiveClient`, не поддерживающий сеансы учётной записи, никогда его не отправляет.

## Коллекции и пути

Для множеств и списков в dotenv используйте массивы JSON:

```dotenv
KTOOLBOX_JOB__ALLOW_LIST='["*.jpg", "*.png"]'
KTOOLBOX_JOB__BLOCK_LIST='["*.zip", "*.psd"]'
KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES='[".zip", ".psd"]'
```

Относительные пути вывода и хранилища разрешаются от рабочего каталога. Задайте путь вложений `./`, чтобы помещать их непосредственно в каталог каждой публикации:

```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

## Шаблоны имён

В шаблонах публикаций и файлов можно использовать `id`, `user`, `service`, `title`, `added`, `published` и `edited`. Пустой `{}` в шаблоне файла означает исходное или последовательное базовое имя.

```dotenv
KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}]{title:.60}
KTOOLBOX_JOB__FILENAME_FORMAT=[{published}]_{title:.60}_{}
KTOOLBOX_JOB__POST_STRUCTURE__FILE={id}_{}
```

Точность спецификации формата Python, например `{title:.60}`, полезна для ограничений длины файловой системы.

## Ограничение загрузок

Размеры задаются в байтах и проверяются до помещения файла в очередь. Не задавайте переменную, чтобы отключить соответствующую границу.

```dotenv
# Минимум 1 КиБ и максимум 1 МиБ.
KTOOLBOX_JOB__MIN_FILE_SIZE=1024
KTOOLBOX_JOB__MAX_FILE_SIZE=1048576

# Получать только обложку публикации, без вложений.
KTOOLBOX_JOB__DOWNLOAD_FILE=True
KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS=False
```

`KTOOLBOX_JOB__CREATOR_CONCURRENCY` управляет параллельными производителями авторов. `KTOOLBOX_JOB__COUNT` отдельно управляет обработчиками файлов, общими для всех авторов.
