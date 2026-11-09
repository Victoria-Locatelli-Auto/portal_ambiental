.PHONY: install migrate seed run test lint fmt shell worker beat reset

install:
	python -m venv .venv && .venv/bin/pip install -U pip && .venv/bin/pip install -r requirements-dev.txt
	cp -n .env.example .env || true

migrate:
	python manage.py makemigrations && python manage.py migrate

seed:            ## carrega catalogo legal + 7 casas + dados das auditorias STX
	python manage.py seed_siga

run:
	python manage.py runserver 0.0.0.0:8000

test:
	pytest --cov=apps --cov-report=term-missing

lint:
	ruff check apps config tests

fmt:
	ruff check --fix apps config tests && ruff format apps config tests

shell:
	python manage.py shell

worker:
	celery -A config worker -l info

beat:
	celery -A config beat -l info

notificar:       ## roda a regua de notificacoes manualmente
	python manage.py enviar_notificacoes

reset:
	rm -f db.sqlite3 && $(MAKE) migrate && $(MAKE) seed
