.PHONY: install test lint clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
