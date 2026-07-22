# Python API

`PawchiveClient` — создаваемый экземпляр асинхронного клиента. Повторно используйте один экземпляр для связанных запросов и закрывайте его с помощью асинхронного контекстного менеджера:

```python
import asyncio

from ktoolbox.api import PawchiveClient


async def main() -> None:
    async with PawchiveClient() as client:
        profile = await client.get_creator_profile("fanbox", "6570768")
        posts = await client.list_creator_posts(profile.service, profile.id, offset=0)
        print(profile.name, len(posts))


asyncio.run(main())
```

Успешные операции JSON возвращают созданные модели Pydantic v2. `get_app_version()` возвращает обычный текст, а `flag_post()` — `None` после успешного ответа `201`.

## Публичные операции

| Метод клиента | Запрос | Результат |
| --- | --- | --- |
| `list_creators()` | `GET /creators` | `list[CreatorSummary]` |
| `list_recent_posts(query=None, offset=None)` | `GET /posts` | `list[Post]` |
| `get_creator_profile(service, creator_id)` | `GET /{service}/user/{creator_id}/profile` | `CreatorProfile` |
| `list_creator_posts(service, creator_id, query=None, offset=None)` | `GET /{service}/user/{creator_id}` | `list[Post]` |
| `list_announcements(service, creator_id)` | `GET /{service}/user/{creator_id}/announcements` | `list[Announcement]` |
| `list_fancards(service, creator_id)` | `GET /{service}/user/{creator_id}/fancards` | `list[Fancard]` |
| `list_creator_links(service, creator_id)` | `GET /{service}/user/{creator_id}/links` | `list[CreatorProfile]` |
| `get_post(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}` | `Post` |
| `search_file_by_hash(file_hash)` | `GET /search_hash/{file_hash}` | `FileSearchResult` |
| `flag_post(service, creator_id, post_id)` | `POST /{service}/user/{creator_id}/post/{post_id}/flag` | `None` |
| `is_post_flagged(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/flag` | `bool` |
| `list_post_revisions(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/revisions` | `list[Revision]` |
| `list_post_comments(service, creator_id, post_id)` | `GET /{service}/user/{creator_id}/post/{post_id}/comments` | `list[Comment]` |
| `get_app_version()` | `GET /app_version` | `str` |

Пять операций OpenAPI, защищённых `cookieAuth`, намеренно исключены: получение избранного учётной записи и добавление или удаление избранных публикаций либо авторов. Отметка публикации входит в публичный контракт и не использует сеанс учётной записи.

## Проверка параметров

- `service`, идентификаторы авторов и публикаций должны содержать хотя бы один непробельный символ.
- Если задан поисковый запрос, он должен содержать не менее трёх символов.
- Смещение API должно быть неотрицательным и кратным 50.
- Хеш файла должен состоять ровно из 64 шестнадцатеричных символов.
- Необязательные параметры запроса со значением `None` не отправляются.

Недопустимые значения вызывают Pydantic `ValidationError` до отправки запроса.

## Контракт ошибок

Все ошибки API наследуются от `PawchiveError`:

| Исключение | Значение |
| --- | --- |
| `PawchiveTransportError` | Ошибка DNS, соединения, TLS или тайм-аут после повторных попыток |
| `PawchiveHTTPError` | Ошибка HTTP без более точного соответствия |
| `PawchiveAuthenticationError` | HTTP `401` или `403` |
| `PawchiveNotFoundError` | HTTP `404` |
| `PawchiveConflictError` | HTTP `409`, включая уже отмеченную публикацию |
| `PawchiveResponseValidationError` | Недопустимый JSON или ответ, не соответствующий модели |

`is_post_flagged()` — единственное намеренное исключение для состояния: `404` преобразуется в `False`. Запросы используют `Accept: application/json`, не следуют перенаправлениям и повторяются только при транспортных ошибках, ответах `429` и `5xx`. Другие ответы `4xx` и ошибки проверки ответа не повторяются.

## Модели и изменение схемы

Созданные модели находятся в `ktoolbox.api.generated` и сохраняют неизвестные поля ответа с помощью настройки Pydantic `extra="allow"`. Клиент передаёт пути этих полей в `drift_reporter`; при интеграции телеметрии можно указать собственную функцию обратного вызова.

Неизменённый исходный контракт находится в `k_generator/pawchive_openapi.json`. Проверяемые исправления совместимости хранятся в `k_generator/pawchive_openapi.overrides.json`, на их основе создаются `k_generator/pawchive_openapi.normalized.json` и детерминированные модели.
