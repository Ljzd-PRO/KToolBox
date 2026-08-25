<div align="center">

# KToolBox

Удобная WebUI, CLI и клиент Python для загрузки общедоступных работ из [Pawchive](https://pawchive.pw/).

[![PyPI](https://img.shields.io/pypi/v/ktoolbox?logo=python)](https://pypi.org/project/ktoolbox/)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ljzd-PRO/KToolBox)](LICENSE)
[![Documentation](https://readthedocs.org/projects/ktoolbox/badge/?version=latest)](https://ktoolbox.readthedocs.io/latest/ru/)

[English](README.md) | [简体中文](README_zh-CN.md) | [繁體中文](README_zh-Hant.md) | [Русский](README_ru.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Français](README_fr.md)

</div>

> [!WARNING]
> KToolBox v1 — новая основная версия, которая ещё недостаточно проверена в реальных условиях. Некоторые функции могут работать с ошибками. Сообщайте о любых проблемах.
>
> Поскольку Kemono больше недоступен, KToolBox теперь по умолчанию использует зеркало Pawchive.

## Начните с WebUI

WebUI — рекомендуемый способ работы с KToolBox. Загрузка работ, синхронизация авторов, расписания, имена, фильтры, ход выполнения и настройки проекта доступны без предварительного изучения команд и конфигурационных файлов.

1. Установите KToolBox с WebUI:

    ```bash
    pipx install "ktoolbox[webui]"
    ```

2. Создайте каталог проекта и запустите его:

    ```bash
    mkdir ktoolbox-project
    cd ktoolbox-project
    ktoolbox webui .
    ```

3. Браузер откроется автоматически. Войдите с именем и случайным паролем, показанными в терминале.
4. Добавьте авторов на странице **Авторы**, затем создайте синхронизацию или загрузку на странице **Задачи**.

Если `ktoolbox.toml` отсутствует, KToolBox создаст его. По умолчанию файлы сохраняются в каталог проекта `downloads`.

![Обзор KToolBox WebUI](docs/assets/webui/40-overview-showcase-desktop-light.png)

Далее прочитайте короткое [руководство по WebUI](https://ktoolbox.readthedocs.io/latest/ru/webui/) или выберите нужный сценарий на [главной странице документации](https://ktoolbox.readthedocs.io/latest/ru/).

## Возможности WebUI

- Загрузка отдельной работы и параллельная синхронизация нескольких авторов.
- Список авторов, правила исключения, форматы имён и несколько планов автоматической синхронизации.
- Постоянная история задач, ход выполнения, общая скорость, повторы, пауза, остановка, перезапуск и безопасная очистка.
- Настройки проекта с понятными описаниями и выбором пути только там, где это уместно.
- Семь языков, адаптивная компоновка, светлая и тёмная темы и необязательный просмотр NSFW-медиа.
- Встроенная служба MCP для Codex, Claude, Cursor, VS Code и совместимых клиентов.

## Необязательная настройка

Для первого запуска достаточно созданных данных входа. Чтобы сохранить постоянный пароль, создайте хеш и добавьте его в `.env` проекта:

```bash
ktoolbox webui hash-password
```

```dotenv
KTOOLBOX_WEBUI__USERNAME=owner
KTOOLBOX_WEBUI__PASSWORD_HASH='$argon2id$...'
```

Для доступа только с этого компьютера добавьте `--host 127.0.0.1`. Встроенный сервер использует HTTP, поэтому для удалённого доступа нужен доверенный сегмент сети или обратный прокси с HTTPS.

## Расширенное использование

CLI остаётся доступной для сценариев и терминала:

```bash
ktoolbox download https://pawchive.pw/fanbox/user/6570768/post/1836570
ktoolbox sync fanbox:123 patreon:456 --length 10
```

Команды описаны в [руководстве CLI](https://ktoolbox.readthedocs.io/latest/ru/commands/guide/), клиенты ИИ — в [руководстве MCP](https://ktoolbox.readthedocs.io/latest/ru/mcp/), программная интеграция — в [Python API](https://ktoolbox.readthedocs.io/latest/ru/api/).

## Обновление с v0

Сохраните резервные копии `.env`, `prod.env` и существующих загрузок. WebUI обнаруживает старые настройки имён и проводит через преобразование конфигурации и каталогов. Перед изменением проекта прочитайте [руководство по переходу на v1](https://ktoolbox.readthedocs.io/latest/ru/migration-v1/); при ошибках используйте [устранение неполадок](https://ktoolbox.readthedocs.io/latest/ru/faq/).

## Разработка

```bash
poetry install --with test,docs,dev
poetry run pytest --cov
poetry run mkdocs build --strict
cd webui && npm ci && npm run test && npm run build
```

Стандартные тесты полностью автономны и не должны обращаться к Pawchive или другим внешним службам.

## Лицензия

KToolBox распространяется по [BSD 3-Clause License](LICENSE).
