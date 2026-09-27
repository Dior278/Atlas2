.PHONY: setup run check doctor browser package

UV ?= uv

setup:
	$(UV) run --locked python scripts/project.py setup

run:
	$(UV) run --locked aparte

check:
	$(UV) run --locked python scripts/project.py check

doctor:
	$(UV) run --locked python scripts/project.py doctor

browser:
	$(UV) run --locked --group browser python scripts/check_atlas_browser.py

package:
	$(UV) run --locked python scripts/release.py
