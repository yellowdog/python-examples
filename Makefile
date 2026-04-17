.DEFAULT_GOAL := no_op

SRC = yellowdog_cli/*.py yellowdog_cli/utils/*.py
TESTS = tests/*.py conftest.py
MANIFEST = LICENSE README.md
BUILD_DIST = build dist yellowdog_cli.egg-info
PYCACHE = __pycache__ yellowdog_cli/__pycache__ yellowdog_cli/utils/__pycache__
TOC_BACKUP = README.md.* README_CLOUDWIZARD.md.*
PYINSTALLER = yellowdog_cli/*.spec yellowdog_cli/build yellowdog_cli/dist

build: $(SRC) $(MANIFEST)
	python -m build

clean:
	rm -rf $(BUILD_DIST) $(PYCACHE) $(TOC_BACKUP) $(PYINSTALLER)

install: build
	uv pip install -U -e ".[jsonnet,cloudwizard]"

uninstall:
	uv pip uninstall yellowdog-cli

format: $(SRC) $(TESTS)
	ruff check --fix $(SRC) $(TESTS)
	ruff format $(SRC) $(TESTS)

#mypy: $(SRC) $(TESTS)
#	mypy $(SRC) $(TESTS)

pypi_upload: clean build
	# '--repository yellowdog-cli' maps into the correct API token for yellowdog-cli uploads
	python -m twine upload --repository yellowdog-cli dist/*

pypi_test_upload: clean build
	python -m twine upload --repository yellowdog-testpypi dist/*

pypi_check: build
	twine check dist/*

toc_all: toc toc_cloudwizard

toc: README.md
	./gh-md-toc --insert README.md

toc_cloudwizard: README_CLOUDWIZARD.md
	./gh-md-toc --insert README_CLOUDWIZARD.md

test:
	pytest -v

tox:
	tox

update:
	uv pip install -U -e ".[dev,jsonnet,cloudwizard]"

no_op:
	# Available targets are: build, clean, format, install, test, tox, uninstall, update, pypi_upload, pypi_check
	# For releases, use: ./release.sh (or ./release.sh --dry-run)
