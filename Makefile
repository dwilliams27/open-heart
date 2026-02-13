.PHONY: all build test install clean clean-all

MOD ?= all

all: build test

build:
	@bash scripts/build-love.sh $(MOD)

test:
	@bash scripts/smoke-test.sh

install:
	@bash scripts/install-mod.sh $(MOD)

clean:
	rm -rf build/

clean-all:
	rm -rf build/ deps/
