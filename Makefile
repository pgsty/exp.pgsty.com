HUGO ?= hugo
BIND ?= 127.0.0.1
PORT ?= 1313
THEME_DIR ?= ../oink
WORKSPACE := $(CURDIR)/go.work

.PHONY: dev build check check-local workspace

# Use the sibling OINK checkout for local development and migration QA. The
# published build resolves the exact version recorded in go.mod instead.
workspace:
	@test -f "$(THEME_DIR)/go.mod" || { \
		echo "OINK theme not found: $(THEME_DIR)" >&2; \
		exit 1; \
	}
	@test -f "$(WORKSPACE)" || go work init .
	@go work use .
	@go work edit -replace=github.com/pgsty/oink="$(THEME_DIR)"

dev: workspace
	@printf 'PG Exporter OINK preview: http://%s:%s/\n' "$(BIND)" "$(PORT)"
	@HUGO_MODULE_WORKSPACE="$(WORKSPACE)" $(HUGO) server \
		--cleanDestinationDir \
		--disableFastRender \
		--renderToMemory \
		--printPathWarnings \
		--bind "$(BIND)" \
		--port "$(PORT)"

build:
	@GOWORK=off $(HUGO) build \
		--minify \
		--cleanDestinationDir

check:
	GOWORK=off go mod verify
	@GOWORK=off $(HUGO) build \
		--minify \
		--cleanDestinationDir \
		--printPathWarnings \
		--printI18nWarnings \
		--panicOnWarning
	python3 bin/check_markdown.py content public
	python3 bin/check_internal_links.py public

check-local: workspace
	@HUGO_MODULE_WORKSPACE="$(WORKSPACE)" $(HUGO) build \
		--minify \
		--cleanDestinationDir \
		--printPathWarnings \
		--printI18nWarnings \
		--panicOnWarning
	python3 bin/check_markdown.py content public
	python3 bin/check_internal_links.py public
