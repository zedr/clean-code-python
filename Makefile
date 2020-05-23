.PHONY: deps clean tests

ENV=.env
PYTHON=python3.7
PYTHON_VERSION=$(shell ${PYTHON} -V | cut -d " " -f 2 | cut -c1-3)
SITE_PACKAGES=${ENV}/lib/python${PYTHON_VERSION}/site-packages
IN_ENV=source ${ENV}/bin/activate;

default: tests

${ENV}:
	@echo "Creating Python environment..." >&2
	@${PYTHON} -m venv ${ENV}
	@echo "Updating pip..." >&2
	@${IN_ENV} pip install -U pip

${SITE_PACKAGES}/pytest.py:
	@${IN_ENV} pip install pytest

deps: ${SITE_PACKAGES}/pytest.py

tests: ${ENV} ${SITE_PACKAGES}/pytest.py
	@${IN_ENV} pytest

clean:
	@rm -rf ${ENV} .env .pytest_cache
