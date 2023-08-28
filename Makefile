.DEFAULT_GOAL := no_op

SRC = yd_commands/*.py
TESTS = tests/*.py
MANIFEST = LICENSE README.md requirements.txt
BUILD_DIST = build dist yellowdog_python_examples.egg-info
PYCACHE = __pycache__
TOC_BACKUP = README.md.*

build: $(SRC) $(MANIFEST)
	python -m build

clean:
	rm -rf $(BUILD_DIST) $(PYCACHE) $(TOC_BACKUP)

install: build
	pip install -U -e .

uninstall:
	pip uninstall -y yellowdog-python-examples

black: $(SRC) $(TESTS)
	black --preview $(SRC) $(TESTS)

isort: $(SRC)
	isort --profile black $(SRC) $(TESTS)

format: isort black

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

toc:
	./gh-md-toc --insert README.md

update:
	pip install -U pip -r requirements.txt -r requirements-dev.txt

no_op:
	# Available targets are: build, clean, install, uninstall, black, pypi_upload, pypi_check
