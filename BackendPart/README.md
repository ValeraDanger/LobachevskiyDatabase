# GorkyGraphAPI

Backend-сервис «умной базы документов».  
Отвечает за авторизацию, хранение и версионирование документов, рабочие пространства пользователей и аудит действий.  
По сути — основной API, к которому ходит фронтенд, а также RAG-сервис.

---

## Основные возможности

- **Авторизация и роли**
  - Регистрация и логин по email/паролю.
  - JWT-токены + refresh-токены.
  - Роли (`admin`, `expert`, `viewer`) и права (`permissions`).
  - Проверка доступов через `require_permission(...)` и `has_document_access(...)`.

- **Документы**
  - Загрузка файлов и сохранение на файловое хранилище.
  - Таблица `documents` + отдельные версии в `document_versions`:
    - статусы документа и версии,
    - признак актуальности,
    - метаданные,
    - уровни доступа (`access_levels`),
    - теги (`tags`).
  - Модерация документов (утверждение/отклонение).
  - Редактирование метаданных с созданием новой версии.
  - Скачивание текущей версии документа.

- **Поиск и RAG**
  - Эндпоинт `/documents/search`:
    - сохраняет запрос пользователя (`workspace_queries`),
    - ходит в внешний RAG-сервис,
    - сопоставляет найденные файлы с документами в БД по `storage_key`,
    - фильтрует результаты по департаментам, датам, доступам, тегам и типу файла.
  - Возвращает:
    - финальный ответ модели,
    - список найденных документов с выдержками (snippets).

- **Рабочее пространство пользователя**
  - `workspace_collections` — подборки документов.
  - `workspace_collection_items` — элементы подборок (конкретная версия + цитата/заметка).
  - `workspace_drafts` — черновики ответов с сохранёнными цитатами.

- **Профиль и аудит**
  - Эндпоинт профиля: информация о пользователе, активности, последних действиях.
  - `audit_events` — лог всех важных операций (просмотр, поиск, скачивание, создание документов, коллекций и т.д.).

- **Справочники**
  - `departments` — департаменты.
  - `roles`, `permissions`, `role_permissions` — ролевая модель.

---

## Технологический стек

- **Язык / фреймворк**: Python 3.11, FastAPI.
- **БД**: PostgreSQL.
- **Доступ к БД**: `asyncpg` + свой лёгкий слой менеджеров (`database/managers`).
- **Схемы и валидация**: Pydantic v2.
- **Аутентификация**: JWT (access + refresh), `bcrypt` для хеширования паролей.
- **HTTP-клиент**: `httpx` (для запросов к RAG-сервису).
- **Контейнеризация**: Docker, Dockerfile в корне проекта.
- **Логирование и конфиг**: `utils.logger`, `utils.config`.

---

## Структура проекта

```text
GorkyGraphAPI/
├── apps/
│   └── api/
│       ├── routers/          # FastAPI-роутеры (эндпоинты)
│       │   ├── auth.py       # /auth — регистрация, логин, refresh
│       │   ├── users.py      # /users — управление пользователями (для админки)
│       │   ├── documents.py  # /documents — загрузка, просмотр, модерация, поиск, скачивание
│       │   ├── workspace.py  # /workspace — подборки, черновики, сохранённые запросы
│       │   ├── departments.py# /departments — справочник департаментов
│       │   ├── profile.py    # /profile — профиль пользователя и активность
│       │   └── health.py     # /health — healthcheck
│       │
│       ├── schemas/          # Pydantic-схемы запросов/ответов
│       │   ├── auth.py
│       │   ├── document.py
│       │   ├── document_view.py
│       │   ├── document_version.py
│       │   ├── documents_upload.py
│       │   ├── documents_search.py
│       │   ├── documents_edit.py
│       │   ├── collection.py
│       │   ├── departments.py
│       │   └── profile.py
│       │
│       ├── core/
│       │   ├── security.py   # JWT-утилиты, зависимость get_current_user, require_permission
│       │   ├── storage.py    # работа с файловым хранилищем документов
│       ├── services/     # "бизнес-сервисы" поверх менеджеров БД
│       │   ├── auth_service.py
│       │   └── profile_service.py
│       │
│       └── __init__.py
│
├── database/
│   ├── managers/             # доступ к БД (один менеджер на сущность)
│   │   ├── base.py           # базовый класс менеджера
│   │   ├── user_manager.py
│   │   ├── document_manager.py
│   │   ├── audit_manager.py
│   │   ├── workspace_manager.py
│   │   └── rbac_manager.py
│   │
│   ├── models/               # модели для строк БД (Document, User, DocumentVersion, AuditEvent...)
│   │   ├── document.py
│   │   ├── document_version.py
│   │   ├── document_metadata.py
│   │   ├── user.py
│   │   ├── rbac.py
│   │   ├── workspace.py
│   │   └── audit.py
│   │
│   └── async_db.py           # создание connection pool и вспомогательные методы
│
│
├── utils/
│   ├── config.py             # чтение переменных окружения
│   └── logger.py             # настройка логгера
│
├── main.py                   # создание FastAPI-приложения, подключение роутеров
├── Dockerfile
├── requirements.txt
├── .env.example              # пример конфигурации
└── README.md                 # этот файл
