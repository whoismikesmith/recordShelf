.PHONY: setup api web build test lint check docker

setup:            ## install backend and web dependencies
	uv sync --all-groups
	cd web && npm install

api:              ## run the API with auto-reload
	uv run recordshelf serve --reload

web:              ## run the Vite dev server (proxies to :8000)
	cd web && npm run dev

build:            ## build the web app into web/dist
	cd web && npm run build

test:             ## backend tests
	uv run pytest -q

lint:             ## lint and format check
	uv run ruff check src tests
	uv run ruff format --check src tests

check: lint test  ## everything CI would run

docker:           ## build the container image
	docker build -t recordshelf .
