HUGO ?= hugo
BIND ?= 127.0.0.1
PORT ?=
THEME_DIR ?= ../oink

.DEFAULT_GOAL := dev

.PHONY: b build c check check-local d debug dev s serve

b: build
c: check
d: debug
s: serve

dev:
	@HUGO_MODULE_REPLACEMENTS='github.com/pgsty/oink -> $(abspath $(THEME_DIR))' $(HUGO) server \
		--renderToMemory \
		--bind "$(BIND)" $(if $(strip $(PORT)),--port "$(PORT)")

debug: dev

serve:
	@GOWORK=off $(HUGO) server --environment production --minify \
		--disableFastRender --disableLiveReload \
		--bind "$(BIND)" $(if $(strip $(PORT)),--port "$(PORT)")

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

check-local:
	@HUGO_MODULE_REPLACEMENTS='github.com/pgsty/oink -> $(abspath $(THEME_DIR))' $(HUGO) build \
		--minify \
		--cleanDestinationDir \
		--printPathWarnings \
		--printI18nWarnings \
		--panicOnWarning
	python3 bin/check_markdown.py content public
	python3 bin/check_internal_links.py public
