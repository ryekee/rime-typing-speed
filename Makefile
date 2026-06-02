.PHONY: dev test install uninstall clean

dev:
	python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

test:
	.venv/bin/pytest -q

# Install the `rspeed` (and short `rts`) command for the current user. Symlinks
# the single stdlib-only script into ~/.local/bin so edits apply live.
# (This installs the CLI; run `rspeed install` afterwards to hook Rime.)
install:
	chmod +x rime_typing_speed.py
	mkdir -p $(HOME)/.local/bin
	ln -sf "$(CURDIR)/rime_typing_speed.py" $(HOME)/.local/bin/rspeed
	ln -sf "$(CURDIR)/rime_typing_speed.py" $(HOME)/.local/bin/rts
	@echo "linked $(HOME)/.local/bin/{rspeed,rts} -> $(CURDIR)/rime_typing_speed.py"

uninstall:
	rm -f $(HOME)/.local/bin/rspeed $(HOME)/.local/bin/rts

clean:
	rm -rf .venv build dist *.egg-info .pytest_cache __pycache__ tests/__pycache__
