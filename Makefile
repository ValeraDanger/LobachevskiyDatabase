ifeq ($(wildcard .env),)
  $(error Файл .env не найден!)
else
  include .env
endif

MIGRATIONS_DIR := ./migrations

DB_URL := postgresql://$(DB_USER):$(DB_PASSWORD)@$(MAKE_DB_HOST):$(MAKE_DB_PORT)/$(DB_NAME)?sslmode=$(SSL_MODE)

.PHONY: migrate rollback migrate_reload
migrate:
	python -m yoyo apply --batch --no-config-file --database "$(DB_URL)" "$(MIGRATIONS_DIR)"

rollback:
	python -m yoyo rollback --batch --no-config-file --database "$(DB_URL)" "$(MIGRATIONS_DIR)"

migrate_reload:
	python -m yoyo rollback --batch --no-config-file --all --database "$(DB_URL)" "$(MIGRATIONS_DIR)"
	python -m yoyo apply    --batch --no-config-file --database "$(DB_URL)" "$(MIGRATIONS_DIR)"

# ------------------------------------------------------------------

NETWORK := app-network
CORE_SERVICES := postgres qdrant
WORK_SERVICES := smart-docs-api rag-api
SERVICES := $(if $(SERVICE),$(SERVICE),$(WORK_SERVICES))

.PHONY: core build up stop rm down ps logs startup

core:
	@echo "Поднимаю core-сервисы: $(CORE_SERVICES)"
	docker compose up -d $(CORE_SERVICES)

build: core
	docker compose build $(SERVICES)

up: build
	docker compose up -d $(SERVICES)

stop:
	docker compose stop $(SERVICES)

rm:
	@echo "Удаляю сервисы: $(SERVICES) (CLEAN=$(CLEAN))"
	-@docker compose stop $(SERVICES)
ifeq ($(CLEAN),1)
	@docker compose rm -fsv $(SERVICES)
	@$(foreach s,$(SERVICES),$(foreach i,$(shell docker compose images -q $(s)),docker rmi -f $(i) || true;))
else
	@docker compose rm -fs $(SERVICES)
endif
	@echo "Готово"

down:
	@echo "Останавливаю всё"
ifeq ($(CLEAN),1)
	docker compose down --volumes --rmi all
else
	docker compose down
endif

ps:
	docker compose ps $(SERVICES)

logs:
	docker compose logs -f $(SERVICES)

startup: up
	@echo "Применяю миграции через migrate_reload"
	@$(MAKE) migrate_reload --no-print-directory
	@echo "Стартовая инициализация завершена"
