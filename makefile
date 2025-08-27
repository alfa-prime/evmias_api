# Makefile for managing Docker-based FastAPI app

# --- Development ---
up:
	docker compose up --build

down:
	docker compose down

bash:
	docker exec -it gateway_app bash

# --- Production ---
up-prod:
	docker compose -f docker-compose.prod.yml up --build -d

down-prod:
	docker compose -f docker-compose.prod.yml down

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f app

bash-prod:
	docker exec -it gateway_app_prod bash


# --- Common ---
clean:
	docker system prune -a --volumes -f
