lint:
    uv run ruff check --fix
    uv run ruff format

typing:
    uv run basedpyright

migration message:
	uv run alembic revision \
	  --autogenerate \
	  --rev-id $(shell python migrations/_get_next_revision_id.py) \
	  --message "{{ message }}"

migrate:
	uv run alembic upgrade head

app-build:
	docker compose build

app-run:
	docker compose stop
	docker compose up -d --remove-orphans

app-stop:
	docker compose stop

app-down:
	docker compose down

app-destroy:
	docker compose down -v --remove-orphans

app-logs:
	docker compose logs -f bot
