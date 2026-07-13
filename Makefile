.PHONY: default
default:

.PHONY: serve
serve: docker-image
	docker run --rm -p 8000:8000 $(DOCKER_IMAGE_TAG) -v serve

.PHONY: install-deps
install-deps:
	pipenv install --dev

.PHONY: update-deps
update-deps:
	pipenv lock --dev && pipenv install --dev

.PHONY: check
check: lint test

.PHONY: lint
lint: lint-black lint-isort lint-pyflakes lint-mypy

LINTED_PATHS = src/enapter_mcp_server tests setup.py

.PHONY: lint-black
lint-black:
	pipenv run black --check $(LINTED_PATHS)

.PHONY: lint-isort
lint-isort:
	pipenv run isort --check $(LINTED_PATHS)

.PHONY: lint-pyflakes
lint-pyflakes:
	pipenv run pyflakes $(LINTED_PATHS)

.PHONY: lint-mypy
lint-mypy:
	pipenv run mypy $(LINTED_PATHS)

.PHONY: test
test: test-unit test-integration

.PHONY: test-unit
test-unit:
	pipenv run pytest -vv --cov --cov-report term-missing tests/unit

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
	sed -E -i 's/mcp-server:v$(RE_SEMVER)/mcp-server:v$(V)/g' README.md
	git cliff --tag "v$(V)" -o CHANGELOG.md
	git add .
	git commit -m "chore(release): bump version to $(V)"
	git tag "v$(V)"

DOCKER_IMAGE_TAG ?= enapter/mcp-server:dev

.PHONY: docker-image
docker-image:
	git submodule update --init --recursive
	docker build -t $(DOCKER_IMAGE_TAG) .
