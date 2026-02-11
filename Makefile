.PHONY: all build test clean clean-all

all: build test

build:
	@bash scripts/build-love.sh

test:
	@bash scripts/smoke-test.sh

clean:
	rm -rf build/

clean-all:
	rm -rf build/ deps/
