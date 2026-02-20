.DEFAULT_GOAL := no_op

SRC = yellowdog_cli/*.py yellowdog_cli/utils/*.py
TESTS = tests/*.py conftest.py
MANIFEST = LICENSE README.md requirements.txt
BUILD_DIST = build dist yellowdog_python_examples.egg-info
PYCACHE = __pycache__ yellowdog_cli/__pycache__ yellowdog_cli/utils/__pycache__
TOC_BACKUP = README.md.* README_CLOUDWIZARD.md.*
PYINSTALLER = yellowdog_cli/*.spec yellowdog_cli/build yellowdog_cli/dist

build: $(SRC) $(MANIFEST)
	python -m build

clean:
	rm -rf $(BUILD_DIST) $(PYCACHE) $(TOC_BACKUP) $(PYINSTALLER)

install: build
	pip install -U -e .

uninstall:
	pip uninstall -y yellowdog-python-examples

black: $(SRC) $(TESTS)
	black --preview $(SRC) $(TESTS)

isort: $(SRC)
	isort --profile black $(SRC) $(TESTS)

format: pyupgrade isort black

#mypy: $(SRC) $(TESTS)
#	mypy $(SRC) $(TESTS)

pypi_upload: clean build
	# '--repository yellowdog-pypi' maps into the correct application token
	# for the YellowDog PyPI account
	python -m twine upload --repository yellowdog-pypi dist/*

pypi_test_upload: clean build
	python -m twine upload --repository yellowdog-testpypi dist/*

pypi_check: build
	twine check dist/*

pyupgrade: $(SRC)
	pyupgrade --exit-zero-even-if-changed --py310-plus $(SRC) $(TESTS)

toc_all: toc toc_cloudwizard

toc: README.md
	./gh-md-toc --insert README.md

toc_cloudwizard: README_CLOUDWIZARD.md
	./gh-md-toc --insert README_CLOUDWIZARD.md

update:
	pip install -U pip -r requirements.txt -r requirements-dev.txt

no_op:
	# Available targets are: build, clean, install, uninstall, black, pypi_upload, pypi_check
