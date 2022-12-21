PYTHON ?= python3

ifeq ($(V),)
	PYTEST_ARGS := -qq
else ifeq ($(V),0)
	PYTEST_ARGS := -qq
else ifeq ($(V),1)
	PYTEST_ARGS := -raP
else ifeq ($(V),2)
	PYTEST_ARGS := -vraP
else
	PYTEST_ARGS := -vvraP
endif

all: lint tests

prereq:
	$(PYTHON) -m pip install --user --upgrade pip
	$(PYTHON) -m pip install --user -r requirements.txt

lint:
	$(PYTHON) -m black -q --check . || ($(PYTHON) -m black .; false)
	$(PYTHON) -m isort -q --check . || ($(PYTHON) -m isort .; false)

test:
	$(PYTHON) -m pytest $(PYTEST_ARGS) test/test_*.py

pkg-build:
	$(PYTHON) -m build

pkg-install:
	$(PYTHON) -m pip install --force-reinstall dist/*.whl

.PHONY: test
