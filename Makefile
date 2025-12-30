.PHONY: help install test run clean deploy backup

help: ## Zobrazit nápovědu
	@echo "Green David App - Příkazy"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instalovat závislosti
	@echo "📦 Instalace závislostí..."
	pip install -r requirements.txt
	@echo "✅ Hotovo!"

setup: ## Nastavit projekt poprvé
	@echo "🔧 Nastavení projektu..."
	cp .env.example .env
	@echo "⚠️  DŮLEŽITÉ: Upravte .env soubor a nastavte SECRET_KEY!"
	@echo "Spusťte: python generate_secret_key.py"

test: ## Spustit testy
	@echo "🧪 Spuštění testů..."
	python test_app.py

run: ## Spustit development server
	@echo "🚀 Spuštění aplikace..."
	@echo "Aplikace běží na http://localhost:5000"
	python main.py

prod: ## Spustit production server
	@echo "🚀 Spuštění produkčního serveru..."
	gunicorn -w 4 -b 0.0.0.0:5000 main:app --timeout 120

clean: ## Vyčistit dočasné soubory
	@echo "🧹 Čištění..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	@echo "✅ Vyčištěno!"

backup: ## Zálohovat databázi
	@echo "💾 Zálohování databáze..."
	@mkdir -p backups
	cp app.db backups/app-$(shell date +%Y%m%d-%H%M%S).db
	@echo "✅ Záloha vytvořena v backups/"

restore: ## Obnovit poslední zálohu
	@echo "♻️  Obnovení poslední zálohy..."
	@if [ -z "$(shell ls -t backups/*.db 2>/dev/null | head -1)" ]; then \
		echo "❌ Žádné zálohy nenalezeny!"; \
		exit 1; \
	fi
	@cp $(shell ls -t backups/*.db | head -1) app.db
	@echo "✅ Databáze obnovena!"

docker-build: ## Sestavit Docker image
	@echo "🐳 Sestavení Docker image..."
	docker build -t green-david-app:latest .

docker-run: ## Spustit v Dockeru
	@echo "🐳 Spuštění v Dockeru..."
	docker-compose up -d

docker-stop: ## Zastavit Docker kontejner
	@echo "🐳 Zastavení Dockeru..."
	docker-compose down

docker-logs: ## Zobrazit Docker logy
	docker-compose logs -f

deploy-render: ## Návod na deploy do Render.com
	@echo "📘 Návod na deployment:"
	@echo "1. Push kód na GitHub"
	@echo "2. Přihlásit se na render.com"
	@echo "3. New → Web Service"
	@echo "4. Připojit GitHub repo"
	@echo "5. Nastavit ENV variables (viz DEPLOYMENT.md)"
	@echo "6. Deploy!"
	@echo ""
	@echo "Podrobnosti viz DEPLOYMENT.md"

security-check: ## Bezpečnostní kontrola
	@echo "🔒 Bezpečnostní kontrola..."
	@echo "Kontrola .env souboru..."
	@if [ ! -f .env ]; then \
		echo "❌ .env soubor neexistuje!"; \
	else \
		echo "✅ .env existuje"; \
	fi
	@echo "Kontrola SECRET_KEY..."
	@if grep -q "SECRET_KEY=your-secret-key-here" .env 2>/dev/null; then \
		echo "⚠️  VAROVÁNÍ: Používáte výchozí SECRET_KEY!"; \
	else \
		echo "✅ SECRET_KEY nastaven"; \
	fi
	@echo "Kontrola admin hesla..."
	@if grep -q "ADMIN_PASSWORD=change-me" .env 2>/dev/null; then \
		echo "⚠️  VAROVÁNÍ: Používáte výchozí admin heslo!"; \
	else \
		echo "✅ Admin heslo nastaveno"; \
	fi

lint: ## Kontrola kódu (pokud máte nainstalován pylint)
	@if command -v pylint >/dev/null 2>&1; then \
		echo "🔍 Kontrola kódu..."; \
		pylint main.py; \
	else \
		echo "⚠️  pylint není nainstalován"; \
	fi

.DEFAULT_GOAL := help
