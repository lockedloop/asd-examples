# ASD Developer Examples

This repository demonstrates **examples of using the ASD tooling** and showcases good Python
development practices for HW developers. For the ASD tool itself, please see the main repository at
[https://github.com/lockedloop/asd](https://github.com/lockedloop/asd).

## Requirements

**Python 3.12 or later is preferred** for best compatibility and performance.

## Note on Setup Complexity

**For small projects**: The extensive tooling configuration described below (Poetry, pre-commit
hooks, linting, etc.) is not necessary. A simple Python `venv` with basic dependencies works
perfectly fine for small scripts and experiments. Use `python3 -m venv venv` and install only what
you need.

**For professional/team projects**: The tooling below helps maintain code quality, consistency, and
makes collaboration easier. It's particularly valuable for hardware development projects where code
reliability is critical.

## Quick Start

### 1. Install Poetry

Poetry is the preferred dependency manager for this project. Install it using one of the following
methods:

**Linux, macOS, Windows (WSL):**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Alternative (via pip):**

```bash
pip install --user poetry
```

**Install Poetry shell plugin (recommended for convenience):**

```bash
poetry self add poetry-plugin-shell
```

This plugin restores the `poetry shell` command that activates the virtual environment.

### 2. Set Up Development Environment

The easiest way to set up your development environment is using the provided Makefile:

```bash
make setup
```

This command will:

<!-- markdownlint-disable MD013 -->

- Install all project dependencies (including development tools)
- Install pre-commit hooks for automatic code quality checks
- Configure your environment for professional Python development

<!-- markdownlint-enable MD013 -->

After setup completes, activate the virtual environment:

```bash
# Option 1: Using poetry shell (requires poetry-plugin-shell installed)
poetry shell

# Option 2: Using Poetry's built-in command
poetry env activate

# Option 3: Run commands without activation
poetry run <command>
```

**Manual setup (if you prefer):**

```bash
# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Activate the virtual environment (requires poetry-plugin-shell)
poetry shell

# Alternative: use Poetry's built-in env activate command
poetry env activate
```

### 3. Install ASD

Choose one of the following installation methods:

**Option 1: Install from Git Repository (Recommended for Users)**

```bash
poetry run pip install git+https://github.com/lockedloop/asd.git
```

**Option 2: Install in Editable Mode from Local Clone (For ASD Development)**

If you have ASD cloned locally (e.g., at `~/Git/asd`), install it in editable mode:

```bash
poetry run pip install -e ~/Git/asd
```

This allows you to make changes to ASD and see them reflected immediately without reinstalling.

**Option 3: Add ASD as Poetry Dependency**

You can also add ASD directly to your `pyproject.toml`:

<!-- markdownlint-disable MD013 -->

```bash
# For regular installation from Git
poetry add git+https://github.com/lockedloop/asd.git

# For editable/development mode from local path
poetry add --editable ~/Git/asd
```

<!-- markdownlint-enable MD013 -->

### 4. Verify Installation

```bash
# Verify ASD is installed correctly
poetry run asd --help
```

**Tip**: Run `asd --help` to see all available ASD commands and options. This is your main reference for understanding what ASD can do.

## Development Tools

This project uses modern Python development tools to ensure code quality:

### Code Formatting and Quality

<!-- markdownlint-disable MD013 -->

- **Ruff**: Fast Python linter and formatter (replaces flake8, isort, black, and more)
- **Mypy**: Static type checking for type safety

<!-- markdownlint-enable MD013 -->

### Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit:

<!-- markdownlint-disable MD013 -->

- Trailing whitespace removal
- End-of-file fixer
- YAML/TOML/JSON validation
- Python code formatting and linting (Ruff)
- Type checking (Mypy)

<!-- markdownlint-enable MD013 -->

## Available Make Commands

This project includes a Makefile with convenient shortcuts:

```bash
make help          # Show all available commands
make install       # Install project dependencies (production)
make install-dev   # Install with development dependencies
make setup         # Complete development environment setup
make format        # Format code with Ruff
make lint          # Run linting checks
make type-check    # Run type checking with Mypy
make test          # Run tests
make test-cov      # Run tests with coverage report
make clean         # Clean up build artifacts and cache files
make pre-commit    # Run pre-commit hooks on all files
make update-deps   # Update all dependencies
```

## Development Workflow

### Before Committing

Pre-commit hooks will automatically run, but you can manually check your code:

```bash
# Format your code
make format

# Run all linting checks
make lint

# Run type checking
make type-check

# Run all pre-commit hooks
make pre-commit
```

### Running Tests

```bash
# Run tests
make test

# Run tests with coverage report
make test-cov
```

### Code Style Standards

<!-- markdownlint-disable MD013 -->

- **Line length**: 100 characters (Python, Markdown, and other source files)
- **Python version**: 3.12+ with type hints
- **Import sorting**: Managed by Ruff (isort rules)
- **Type checking**: Strict mode enabled with Mypy

<!-- markdownlint-enable MD013 -->

## Project Structure

```text
asd-examples/
├── .editorconfig              # Editor configuration for consistent formatting
├── .gitignore                 # Git ignore patterns
├── .markdownlint.json         # Markdown linting configuration
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── pyproject.toml             # Poetry dependencies and tool configurations
├── Makefile                   # Development task shortcuts
├── README.md                  # This file
└── examples/                  # ASD usage examples
```

## Configuration Files

### pyproject.toml

Contains all project metadata, dependencies, and tool configurations for:

<!-- markdownlint-disable MD013 -->

- Poetry (dependency management)
- Ruff (linting and formatting)
- Mypy (type checking)
- Pytest (testing)
- Coverage (code coverage)

<!-- markdownlint-enable MD013 -->

### .pre-commit-config.yaml

Defines pre-commit hooks that run automatically before each commit to ensure code quality.

### .editorconfig

Ensures consistent coding styles across different editors and IDEs.

### .markdownlint.json

Configures Markdown linting rules with 100-character line length.

## Alternative: Using Standard venv

If you prefer not to use Poetry, you can use Python's built-in venv:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies (manually, since no requirements.txt)
pip install ruff mypy pre-commit pytest pytest-cov

# Install ASD
pip install git+https://github.com/lockedloop/asd.git
```

**Note**: Poetry is strongly recommended for this project as it handles dependency management,
virtual environments, and tool configuration in a unified way.

## Contributing

When contributing to this repository:

1. Ensure all pre-commit hooks pass
2. Write tests for new functionality
3. Update documentation as needed
4. Follow the code style standards (enforced by tools)
5. Run `make pre-commit` before pushing

## Resources

<!-- markdownlint-disable MD013 -->

- [ASD Main Repository](https://github.com/lockedloop/asd)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)

<!-- markdownlint-enable MD013 -->
