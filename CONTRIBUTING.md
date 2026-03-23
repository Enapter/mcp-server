# Contributing to Enapter MCP Server

First off, thank you for considering contributing to the Enapter MCP Server! We
appreciate your time and effort.

The following is a set of guidelines for contributing to this project.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.14**
- **Pipenv**
- **Docker** (optional, for building the container image)

### Setting up your environment

We automate our development workflow using `make`. Run the following command to
install both the project and development dependencies:

```bash
make install-deps
```

If you need to update dependencies later, you can use:

```bash
make update-deps
```

## Development Workflow

You can inspect the `Makefile` and `Pipfile` to see all available targets and
the exact tools used for code quality, formatting, and testing.

### Formatting & Linting

Before committing your changes, please run the following command to ensure your
code complies with our standards:

```bash
make check
```

If you only want to run the linters, you can use:

```bash
make lint
```

### Testing

Run all tests:

```bash
make test
```

## Making Changes

1. Create a new branch for your feature or bug fix: `git checkout -b feature/my-new-feature` or `fix/issue-description`.
2. Make your changes and write tests if applicable.
3. Ensure all tests and linters pass (`make check`).
4. Commit your changes. Please use conventional commit messages, as they are
   used to generate the changelog.

## Releasing and Versioning

When preparing a new release, you can bump the version (typically done by
maintainers):

```bash
make bump-version V=X.Y.Z
```

## Docker Builds

If you need to build the Docker image locally for testing or deployment, you
can use the provided Makefile target:

```bash
make docker-image
```

Thank you for contributing!
