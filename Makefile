.PHONY: help install db-up db-down db-logs run test clean

# Shows this help menu by default when you just type 'make'
help:
	@echo "Ledger API Commands:"
	@echo "--------------------------------------------------------"
	@echo "  make install  - Install Python dependencies"
	@echo "  make db-up    - Start the PostgreSQL database via Docker"
	@echo "  make db-down  - Stop the database and wipe the data"
	@echo "  make db-logs  - Tail the database container logs"
	@echo "  make run      - Start the FastAPI server locally"
	@echo "  make test     - Run the full pytest suite"
	@echo "  make clean    - Remove cached Python & pytest files"
	@echo "--------------------------------------------------------"

install:
	pip install -r requirements.txt

db-up:
	docker-compose up -d db

db-down:
	docker-compose down -v

db-logs:
	docker-compose logs -f db

run:
	uvicorn app.main:app --reload

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +