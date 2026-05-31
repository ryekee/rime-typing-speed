.PHONY: dev test install uninstall clean

dev:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

test:
	.venv/bin/pytest -q

install:
	pipx install .

uninstall:
	pipx uninstall rime-speed

clean:
	rm -rf .venv build dist *.egg-info .pytest_cache __pycache__ tests/__pycache__
