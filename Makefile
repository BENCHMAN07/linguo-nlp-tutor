.PHONY: setup scrape build-data run test
setup:
	python -m pip install -r requirements.txt
	python -m playwright install chromium
	python scripts/download_models.py

scrape:
	python scraper/scrape.py

build-data:
	python scripts/build_questions.py
	python scripts/validate_data.py
	python scripts/seed_demo.py

run:
	python -m uvicorn backend.app.main:app --reload

test:
	python -m pytest
