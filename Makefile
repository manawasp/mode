PROJ ?= mode
PGPIDENT ?= "Faust Security Team"
PYTHON ?= python
PYTEST ?= py.test
PIP ?= pip
GIT ?= git
TOX ?= tox
NOSETESTS ?= nosetests
ICONV ?= iconv
MYPY ?= mypy

TESTDIR ?= t
README ?= README.rst
README_SRC ?= "docs/templates/readme.txt"
CONTRIBUTING ?= CONTRIBUTING.rst
CONTRIBUTING_SRC ?= "docs/contributing.rst"
COC ?= CODE_OF_CONDUCT.rst
COC_SRC ?= "docs/includes/code-of-conduct.txt"
DOCUMENTATION=Documentation

all: help

help:
	@echo "docs                 - Build documentation."
	@echo "test-all             - Run tests for all supported python versions."
	@echo "develop              - Install all dependencies into current virtualenv."
	@echo "distcheck ---------- - Check distribution for problems."
	@echo "  test               - Run unittests using current python."
	@echo "  lint ------------  - Check codebase for problems."
	@echo "    apicheck         - Check API reference coverage."
	@echo "    readmecheck      - Check README.rst encoding."
	@echo "    contribcheck     - Check CONTRIBUTING.rst encoding"
	@echo "    ruff             - Check code for syntax and style errors."
	@echo "readme               - Regenerate README.rst file."
	@echo "contrib              - Regenerate CONTRIBUTING.rst file"
	@echo "coc                  - Regenerate CODE_OF_CONDUCT.rst file"
	@echo "clean-dist --------- - Clean all distribution build artifacts."
	@echo "  clean-git-force    - Remove all uncomitted files."
	@echo "  clean ------------ - Non-destructive clean"
	@echo "    clean-pyc        - Remove .pyc/__pycache__ files"
	@echo "    clean-docs       - Remove documentation build artifacts."
	@echo "    clean-build      - Remove setup artifacts."
	@echo "release              - Make PyPI release."

clean: clean-docs clean-pyc clean-build

clean-dist: clean clean-git-force

release:
	$(PYTHON) register sdist bdist_wheel upload --sign --identity="$(PGPIDENT)"

. PHONY: deps-default
deps-default:
	$(PIP) install -U -e "."

. PHONY: deps-docs
deps-docs:
	$(PIP) install -U -r requirements-docs.txt

. PHONY: deps-test
deps-test:
	$(PIP) install -U -r requirements-test.txt

. PHONY: deps-extras
deps-extras:
	$(PIP) install -U -r requirements/extras/eventlet.txt
	$(PIP) install -U -r requirements/extras/uvloop.txt

. PHONY: develop
develop: deps-default deps-dist deps-docs deps-test deps-extras
	$(PYTHON) develop

. PHONY: Documentation
Documentation:
	mkdocs build

. PHONY: docs
docs: Documentation

. PHONE: serve-docs
serve-docs:
	mkdocs serve

clean-docs:
	-rm -rf "$(SPHINX_BUILDDIR)"

ruff:
	ruff check . --fix

lint: ruff apicheck readmecheck

clean-readme:
	-rm -f $(README)

readmecheck:
	$(ICONV) -f ascii -t ascii $(README) >/dev/null

readme: clean-readme $(README) readmecheck

clean-contrib:
	-rm -f "$(CONTRIBUTING)"

contrib: clean-contrib $(CONTRIBUTING)

clean-coc:
	-rm -f "$(COC)"

coc: clean-coc $(COC)

clean-pyc:
	-find . -type f -a \( -name "*.pyc" -o -name "*$$py.class" \) | xargs rm
	-find . -type d -name "__pycache__" | xargs rm -r

removepyc: clean-pyc

clean-build:
	rm -rf build/ dist/ .eggs/ *.egg-info/ .tox/ .coverage cover/

clean-git:
	$(GIT) clean -xdn

clean-git-force:
	$(GIT) clean -xdf

test-all: clean-pyc
	$(TOX)

test:
	$(PYTEST) .

cov:
	$(PYTEST) -x --cov="$(PROJ)" --cov-report=html

build:
	$(PYTHON) sdist bdist_wheel

distcheck: lint test clean

dist: readme contrib clean-dist build

typecheck:
	$(PYTHON) -m $(MYPY) -p $(PROJ)

.PHONY: requirements
requirements:
	$(PIP) install --upgrade pip;\
	$(PIP) install -r requirements.txt
