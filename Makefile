.PHONY: install install-game install-backend install-bot install-site up-infra down-infra run-game run-backend run-redirect run-bot run-site

PYTHON ?= python3

install:
	pip install -r requirements.txt

install-game:
	pip install -r requirements/game.txt

install-backend:
	pip install -r requirements/backend.txt

install-bot:
	pip install -r requirements/bot.txt

install-site:
	pip install -r requirements/site.txt

up-infra:
	docker compose up -d postgres redis

down-infra:
	docker compose down

run-game:
	cd dnd1 && $(PYTHON) manage.py runserver 0.0.0.0:7000

run-backend:
	cd back-end/app && uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-redirect:
	cd back-end/app && uvicorn redirect:app1 --reload --host 0.0.0.0 --port 10000

run-bot:
	cd tg_bot && $(PYTHON) bot.py

run-site:
	cd site && streamlit run main.py --server.port 8501
