HUGO ?= hugo

.PHONY: dev build check

dev:
	$(HUGO) server

build:
	$(HUGO) build --minify --cleanDestinationDir

check:
	go mod verify
	$(HUGO) build --minify --cleanDestinationDir --printPathWarnings --printI18nWarnings --panicOnWarning
	python3 bin/check_markdown.py content public
	python3 bin/check_internal_links.py public
