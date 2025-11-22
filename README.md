# GorkyGraph Platform

## Быстрый старт

Для быстрого запуска всей платформы (Backend + RAG + PostgreSQL +
Qdrant):

``` bash
# 1. Подготовьте .env файлы
cp .env.example .env
cd BackendPart && cp .env.example .env && cd ..
cd MLPart && cp .env.example .env && cd ..

# 2. Запустите все сервисы и примените миграции 
# (важно делать из под окружения с установленным yoyo-migrations)
make startup

# 3. Проверьте статус контейнеров
make ps
```

После запуска сервисы будут доступны по адресам:

-   Backend API (BackendPart): http://localhost:8000/docs\
-   RAG API (MLPart): http://localhost:8080/docs\

------------------------------------------------------------------------


Монорепозиторий из двух связанных сервисов:

-   **BackendPart** --- backend «умной базы документов» (авторизация,
    документы, рабочие пространства, аудит, поиск и интеграция с RAG).
-   **MLPart** --- модульная RAG-система для обработки
    документов, извлечения сущностей и построения графовой + векторной
    базы знаний (Qdrant + LLM).

Сервисы запускаются совместно через Docker Compose, используют общую
PostgreSQL и единое файловое хранилище документов.

------------------------------------------------------------------------

## 1. Структура репозитория

``` text
.
├── BackendPart/        # Backend-сервис (FastAPI)
├── MLPart/                   # RAG-сервис
├── migrations/           
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

------------------------------------------------------------------------

## 2. Требования

-   Docker + Docker Compose\
-   Make\
-   Python + yoyo-migrations

------------------------------------------------------------------------

## 3. Настройка окружения

### Корневой `.env`

    cp .env.example .env

### `.env` для BackendPart

    cd BackendPart
    cp .env.example .env

### `.env` для MLPart

    cd MLPart
    cp .env.example .env

------------------------------------------------------------------------

## 4. Makefile --- команды

### Миграции

    make migrate
    make rollback
    make migrate_reload

### Управление сервисами

    make core
    make build
    make up
    make stop
    make rm
    make down
    make ps
    make logs

### Полный запуск

    make startup

------------------------------------------------------------------------

## 5. URLы после запуска

-   Backend API: http://localhost:8000/docs\
-   RAG API: http://localhost:8080
