.PHONY: install run test

PROJECT ?= biopsy-analysis

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	python main.py -p $(PROJECT)

test:
	pytest
