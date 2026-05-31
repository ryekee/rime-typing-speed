.PHONY: dev test install uninstall clean

dev:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

test:
	.venv/bin/pytest -q

# Install the `rime-speed` command for the current user. Symlinks the single
# stdlib-only script into ~/.local/bin so edits to rime_speed.py apply live.
# (This installs the CLI; run `rime-speed install` afterwards to hook Rime.)
install:
	chmod +x rime_speed.py
	mkdir -p $(HOME)/.local/bin
	ln -sf "$(CURDIR)/rime_speed.py" $(HOME)/.local/bin/rime-speed
	@echo "linked $(HOME)/.local/bin/rime-speed -> $(CURDIR)/rime_speed.py"

uninstall:
	rm -f $(HOME)/.local/bin/rime-speed

clean:
	rm -rf .venv build dist *.egg-info .pytest_cache __pycache__ tests/__pycache__
