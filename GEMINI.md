# Project: package-scan

## Project Overview

`package-scan` is a Python-based command-line interface (CLI) tool designed to detect compromised packages across multiple ecosystems including npm (JavaScript), Maven/Gradle (Java), and pip (Python). It scans projects against a CSV database of known compromised packages from various supply chain attacks.

The main technologies used are:
- **Python:** The core language for the application.
- **Click:** A Python package for creating command-line interfaces.
- **semantic_version:** A library for parsing and comparing NPM semantic versioning (semver) strings.
- **lxml:** For parsing Maven pom.xml files (optional dependency).
- **PyYAML:** For parsing pnpm and conda files (optional dependency).
- **toml/packaging:** For parsing Python package files (optional dependency).

The project uses a modular architecture with ecosystem-specific adapters:
- `cli.py` - Main multi-ecosystem CLI
- `core/` - Shared components (ThreatDatabase, ReportEngine, Finding model)
- `adapters/` - Ecosystem-specific scanners (npm, java, python)

## Building and Running

### Installation

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install the package in editable mode:**
    This will install the necessary dependencies and make the `npm-scan` command available in your shell.
    ```bash
    pip install -e .
    ```

### Running the Scanner

The primary way to run the scanner is through the `package-scan` command:

-   **Scan the current directory (all ecosystems):**
    ```bash
    package-scan
    ```

-   **Scan a specific directory:**
    ```bash
    package-scan --dir /path/to/your/project
    ```

-   **Scan for specific threat:**
    ```bash
    package-scan --threat sha1-Hulud
    ```

-   **Scan specific ecosystem:**
    ```bash
    package-scan --ecosystem npm
    package-scan --ecosystem maven,pip  # Multiple ecosystems
    ```

-   **Specify a different CSV file and output file:**
    ```bash
    package-scan --csv /path/to/custom.csv --output /tmp/report.json
    ```

You can also run via Python module:

```bash
python -m package_scan.cli --help
```

Legacy commands are still available for backward compatibility:
- `npm-scan` - npm-only scanning (redirects to main CLI with npm ecosystem)
- `hulud-scan` - alias for package-scan

## Development Conventions

-   **Packaging:** The project uses `setuptools` for packaging, with configuration in `pyproject.toml`.
-   **CLI:** The command-line interface is built using the `click` library. The main entry point is the `cli` function in `cli.py`.
-   **Architecture:** Modular design with ecosystem-specific adapters implementing a common interface.
-   **Dependencies:**
    - Core dependencies: click, semantic_version
    - Optional dependencies: pyyaml (pnpm), lxml (maven), toml/packaging (python ecosystem)
-   **Code Style:** The code is well-structured with clear separation of concerns.
-   **Testing:** Run tests with `pytest` from the project root. Tests are located in the `tests/` directory.
