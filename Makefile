.PHONY: help up up-prd down logs api-test web-build etl-dry seed-note

help:
	@echo "AS App targets:"
	@echo "  make up          - Dev stack (db+api+web) via docker-compose.yml"
	@echo "  make up-prd      - Prod-shaped stack (needs .env.prd)"
	@echo "  make down        - Stop dev stack (keeps volumes)"
	@echo "  make logs        - Tail api+web"
	@echo "  make api-test    - pytest inside api container"
	@echo "  make web-build   - npm run build in frontend/"
	@echo "  make etl-dry     - Dry-run MySQL→Postgres core ETL"

up:
	docker compose up -d --build

up-prd:
	@test -f .env.prd || (echo "Missing .env.prd — copy .env.prd.example" >&2; exit 1)
	docker compose -f docker-compose.prd.yml --env-file .env.prd up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100 api web

api-test:
	docker compose exec -T api pytest -q

web-build:
	cd frontend && npm run build

etl-dry:
	cd scripts/etl && python3 migrate_core.py --dry-run

seed-note:
	@echo "Seed runs in api entrypoint unless SKIP_SEED=1 (demo SKUs: DEMO-*)"
