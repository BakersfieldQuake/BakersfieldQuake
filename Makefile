# Local macOS app build for testing. Release DMGs come only from CI (see AGENTS.md).
#
#   make app              build BAKOQUAKE.app (signed, not notarized) and launch it
#   make run              launch the last build
#   make app TAG=<tag>    build from a specific release instead of the newest one with a macOS zip
#   make app NO_ZIP=0     allow the full ~1 GB release zip even when main matches origin/main

WORK ?= $(CURDIR)/build
APP  := $(WORK)/out/BAKOQUAKE.app

.PHONY: app build run

app: build run

# The updater is frozen with uv's python-build-standalone 3.12 (targets macOS 11.0); build_app.sh refuses
# Pythons built for anything newer than 13.0, which rules out pyenv/Homebrew builds.
build:
	@set -e; \
	py=$$(uv python find --managed-python 3.12 2>/dev/null) || { echo "run: uv python install 3.12"; exit 1; }; \
	tag="$(TAG)"; \
	if [ -z "$$tag" ]; then \
	  for t in $$(gh release list --exclude-drafts -L 20 --json tagName -q '.[].tagName'); do \
	    gh release view "$$t" --json assets -q '.assets[].name' | grep -qx BAKOQUAKE-macos-arm64.zip && { tag=$$t; break; }; \
	  done; \
	fi; \
	[ -n "$$tag" ] || { echo "no release with BAKOQUAKE-macos-arm64.zip"; exit 1; }; \
	no_zip="$(NO_ZIP)"; \
	if [ -z "$$no_zip" ]; then \
	  no_zip=0; [ "$$(git rev-parse main)" = "$$(git rev-parse origin/main)" ] && no_zip=1; \
	fi; \
	echo "release $$tag, python $$py, NO_ZIP=$$no_zip"; \
	SKIP_NOTARIZE=1 NO_ZIP=$$no_zip WORK="$(WORK)" PYTHON="$$py" source/mac/build_app.sh "$$tag"

run:
	open "$(APP)"
