.PHONY: up down logs shell migrate makemigrations test lint superuser

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f api

shell:
	docker compose exec api python manage.py shell

migrate:
	docker compose exec api python manage.py migrate

makemigrations:
	docker compose exec api python manage.py makemigrations

test:
	pytest tests/ -v --cov=apps --cov-report=term-missing

lint:
	ruff check .

superuser:
	docker compose exec api python manage.py createsuperuser

schema:
	python manage.py spectacular --file schema.yml
