# Local macOS app build from this repo, for testing. Release DMGs come only from CI (see AGENTS.md).
#
#   make app     assemble the game data from the repo, build BAKOQUAKE.app (signed, not notarized, no DMG), launch it
#   make run     launch the last build, without the launcher's update from the GitHub release
#   make base    (re)download the base package; `make app` does it once on a fresh checkout
#
# build/base holds the blobs the repo does not (base pk3s, maps, zz_*.pk3s with no builder here); `make build` first
# brings it up to the latest release with tools/bq_update.py.
# source/mm_tools/assemble_local_package.sh lays the repo over a clone of it in build/pkg.

WORK ?= $(CURDIR)/build
BASE := $(WORK)/base/BAKOQUAKE

# Pick the base package for this OS. Release assets: BAKOQUAKE-macos-arm64.zip, BAKOQUAKE-linux-x86_64.zip.
UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
  BASE_ZIP := BAKOQUAKE-macos-arm64.zip
else
  BASE_ZIP := BAKOQUAKE-linux-x86_64.zip
endif
PKG  := $(WORK)/pkg/BAKOQUAKE
APP  := $(WORK)/out/BAKOQUAKE.app
# The updater is frozen with uv's python-build-standalone 3.12 (targets macOS 11.0); build_app.sh refuses
# Pythons built for anything newer than 13.0, which rules out pyenv/Homebrew builds.
PY = $(shell uv python find --managed-python 3.12 2>/dev/null)

.PHONY: app build run base

app: build run

build: $(BASE)/BakersfieldQuake/bakersfield.pk3
	@[ -n "$(PY)" ] || { echo "run: uv python install 3.12"; exit 1; }
	@# Bring the base up to the latest release with the game's own updater: only changed files (maps, pk3s) download.
	@# Exit 3 means it updated something.
	"$(PY)" -I tools/bq_update.py --root "$(BASE)" --no-gui </dev/null || [ $$? = 3 ]
	WORK="$(WORK)" PYTHON="$(PY)" source/mm_tools/assemble_local_package.sh "$(BASE)" "$(PKG)"
ifeq ($(UNAME),Darwin)
	SKIP_NOTARIZE=1 NO_DMG=1 PKG_DIR="$(PKG)" WORK="$(WORK)" PYTHON="$(PY)" \
	  source/mac/build_app.sh "local-$$(date +%Y%m%d%H%M%S)-$$(git rev-parse --short HEAD)"
endif

# BQ_NO_UPDATE: the launcher would otherwise patch the local build back to the latest GitHub release.
run:
	open --env BQ_NO_UPDATE=1 "$(APP)"

# Fresh checkout only: the newest release's macOS package supplies the base blobs.
$(BASE)/BakersfieldQuake/bakersfield.pk3:
	$(MAKE) base

base:
	@set -e; \
	for t in $$(gh release list --exclude-drafts -L 20 --json tagName -q '.[].tagName'); do \
	  gh release view "$$t" --json assets -q '.assets[].name' | grep -qx "$(BASE_ZIP)" && { tag=$$t; break; }; \
	done; \
	[ -n "$$tag" ] || { echo "no release with $(BASE_ZIP)"; exit 1; }; \
	url=$$(gh release view "$$tag" --json assets -q '.assets[] | select(.name=="$(BASE_ZIP)") | .apiUrl'); \
	echo "base: $$tag ($(BASE_ZIP))"; \
	rm -rf "$(WORK)/dl" "$(WORK)/base"; \
	mkdir -p "$(WORK)/dl" "$(WORK)/base"; \
	curl -L --fail --retry 3 -H "Authorization: Bearer $$(gh auth token)" -H "Accept: application/octet-stream" \
	  "$$url" -o "$(WORK)/dl/$(BASE_ZIP)"; \
	case "$(UNAME)" in \
	  Darwin) ditto -x -k "$(WORK)/dl/$(BASE_ZIP)" "$(WORK)/base" ;; \
	  *)      unzip -o -q "$(WORK)/dl/$(BASE_ZIP)" -d "$(WORK)/base" ;; \
	esac; \
	rm -rf "$(WORK)/dl"
