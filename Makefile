.PHONY: default
default:

.PHONY: install-deps
install-deps:
	pipenv install --dev

.PHONY: update-deps
update-deps:
	pipenv update --dev

.PHONY: check
check: lint test

.PHONY: lint
lint: lint-black lint-isort lint-pyflakes lint-mypy

.PHONY: lint-black
lint-black:
	pipenv run black --check .

.PHONY: lint-isort
lint-isort:
	pipenv run isort --check .

.PHONY: lint-pyflakes
lint-pyflakes:
	pipenv run pyflakes .

.PHONY: lint-mypy
lint-mypy:
	pipenv run mypy setup.py
	pipenv run mypy tests
	pipenv run mypy src/enapter_mcp_server

.PHONY: test
test: test-integration

.PHONY: test-integration
test-integration:
	pipenv run pytest -vv --capture=no tests/integration

.PHONY: get-pipenv
get-pipenv:
	curl https://raw.githubusercontent.com/pypa/pipenv/master/get-pipenv.py | python

RE_SEMVER = [0-9]+.[0-9]+.[0-9]+(-[a-z0-9]+)?

.PHONY: bump-version
bump-version:
ifndef V
	$(error V is not defined)
endif
	sed -E -i 's/__version__ = "$(RE_SEMVER)"/__version__ = "$(V)"/g' src/enapter_mcp_server/__init__.py

DOCKER_IMAGE_TAG ?= enapter/mcp-server:dev

.PHONY: docker-image
docker-image:
	docker build -t $(DOCKER_IMAGE_TAG) .
