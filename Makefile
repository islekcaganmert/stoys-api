all:
	@echo "Possible Commands:"
	@echo "\t build"
	@echo "\t install"
	@echo "\t test"

build:
	@rm -rf ./dist/*
	@python3 -m build

install:
	@python3 -m pip uninstall stoys -y
	@python3 -m pip install dist/*.whl
