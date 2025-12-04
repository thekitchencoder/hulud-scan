# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

hulud-scan is a Python CLI tool for detecting compromised packages across multiple ecosystems. It scans JavaScript (npm), Java (Maven/Gradle), and Python (pip/poetry/pipenv/conda) projects against a CSV database of known compromised packages.

**Supported Ecosystems:**
- **npm**: JavaScript/Node.js packages (package.json, lockfiles, node_modules)
- **maven**: Java packages via Maven (pom.xml) and Gradle (build.gradle)
- **pip**: Python packages via pip, Poetry, Pipenv, and conda

## Development Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install in editable mode with all optional dependencies:
   ```bash
   pip install -e ".[all]"
   # Or just core dependencies:
   pip install -e .
   ```

3. Verify installation:
   ```bash
   hulud-scan --help
   hulud-scan --list-ecosystems
   ```

## Running the Tool

### Multi-Ecosystem Scanning

**Auto-detect and scan all ecosystems:**
```bash
hulud-scan                                    # Scan current directory
hulud-scan --dir /path/to/project             # Scan specific directory
hulud-scan --csv /path/to/custom.csv          # Use custom threat database
hulud-scan --output custom_report.json        # Custom output file
hulud-scan --no-save                          # Don't save JSON report
```

**Scan specific ecosystem:**
```bash
hulud-scan --ecosystem npm                    # npm only
hulud-scan --ecosystem maven                  # Maven/Gradle only
hulud-scan --ecosystem pip                    # Python only
hulud-scan --ecosystem npm,maven,pip          # Multiple ecosystems
```

**List supported ecosystems:**
```bash
hulud-scan --list-ecosystems
```

**List compromised packages in database:**
```bash
hulud-scan --list-affected-packages           # Formatted display
hulud-scan --list-affected-packages-csv       # Raw CSV output
```

### Legacy npm-only Command

For backward compatibility, the original `npm-scan` command is still available:
```bash
npm-scan --dir /path/to/project
```

### Docker Usage

**Build image:**
```bash
docker build -t hulud-scan .
```

**Scan a project:**
```bash
# Scan current directory
docker run --rm -v "$(pwd):/workspace" hulud-scan

# Scan specific directory
docker run --rm -v "/path/to/project:/workspace" hulud-scan

# Scan specific ecosystem
docker run --rm -v "$(pwd):/workspace" hulud-scan --ecosystem maven

# Get help
docker run --rm hulud-scan --help
```

**Output:**
- Reports saved as `./hulud_scan_report.json` in the mounted workspace
- Use `--output` to change report filename
- Use `--no-save` to skip saving (console output only)

## Architecture

### Modular Design

The scanner uses a modular architecture with ecosystem-specific adapters:

```
src/hulud_scan/
├── cli.py                         # Multi-ecosystem CLI
├── core/                          # Shared components
│   ├── models.py                  # Finding, Remediation dataclasses
│   ├── threat_database.py         # Multi-ecosystem CSV loading
│   └── report_engine.py           # Unified reporting
├── adapters/                      # Ecosystem-specific scanners
│   ├── base.py                    # EcosystemAdapter interface
│   ├── npm_adapter.py             # JavaScript/Node.js
│   ├── java_adapter.py            # Maven/Gradle
│   └── python_adapter.py          # pip/poetry/pipenv/conda
└── scan_npm_threats.py            # Legacy npm-only scanner (deprecated)
```

### Core Components

**ThreatDatabase** (`core/threat_database.py`):
- Loads CSV with format: `ecosystem,name,version`
- Supports legacy format: `Package Name,Version` (defaults to npm)
- Filters threats by ecosystem
- Methods: `load()`, `get_compromised_versions()`, `get_all_packages()`, `get_ecosystems()`

**ReportEngine** (`core/report_engine.py`):
- Aggregates findings from all adapters
- Generates formatted console reports grouped by ecosystem
- Exports JSON reports with ecosystem sections
- Methods: `add_findings()`, `print_report()`, `save_report()`

**Finding Model** (`core/models.py`):
- Standardized finding structure across all ecosystems
- Fields: ecosystem, finding_type (manifest/lockfile/installed), file_path, package_name, version, match_type (exact/range), declared_spec, remediation
- Converts to dictionary for JSON export

### Ecosystem Adapters

Each adapter implements the `EcosystemAdapter` interface:

#### NpmAdapter (`adapters/npm_adapter.py`)

**Supported Formats:**
- `package.json`: Manifest with dependencies, devDependencies, peerDependencies, optionalDependencies
- `package-lock.json`: npm lockfile (v1/v2/v3 formats)
- `yarn.lock`: Yarn lockfile
- `pnpm-lock.yaml`: pnpm lockfile (requires PyYAML)
- `node_modules/`: Installed packages

**Version Matching:**
- Uses `semantic_version.NpmSpec` for npm semver ranges (^, ~, >=, etc.)
- Handles scoped packages (@org/package)
- Supports exact versions and version ranges

**Key Methods:**
- `detect_projects()`: Finds directories with package.json
- `scan_project()`: Scans manifests, lockfiles, and node_modules
- `_scan_package_json()`: Parses JSON and checks dependencies
- `_scan_package_lock_json()`: Handles v1/v2/v3 lockfile formats
- `_scan_yarn_lock()`: Regex-based yarn.lock parsing
- `_scan_pnpm_lock_yaml()`: YAML parsing for pnpm
- `_scan_node_modules()`: Recursively scans installed packages

#### JavaAdapter (`adapters/java_adapter.py`)

**Supported Formats:**
- `pom.xml`: Maven manifest
- `build.gradle`: Gradle Groovy DSL
- `build.gradle.kts`: Gradle Kotlin DSL
- `gradle.lockfile`: Gradle 7+ lockfile

**Version Matching:**
- Maven version ranges: `[1.0,2.0)`, `[1.0,)`, `(,2.0)` with inclusive/exclusive bounds
- Gradle dynamic versions: `1.2.+` converted to regex patterns
- Exact versions: `1.2.3`

**Key Methods:**
- `detect_projects()`: Finds directories with pom.xml or build.gradle
- `scan_project()`: Scans Maven and Gradle files
- `_scan_pom_xml()`: XML parsing with namespace handling
- `_scan_gradle_build()`: Regex-based Groovy/Kotlin DSL parsing
- `_scan_gradle_lockfile()`: Parses Gradle lockfile format
- `_is_maven_range()`: Detects Maven version ranges
- `_get_matching_maven_versions()`: Range matching logic

#### PythonAdapter (`adapters/python_adapter.py`)

**Supported Formats:**
- `requirements.txt`, `requirements-*.txt`: pip requirements files
- `pyproject.toml`: Poetry manifest (tool.poetry.dependencies)
- `poetry.lock`: Poetry lockfile (TOML format)
- `Pipfile`: pipenv manifest (TOML format)
- `Pipfile.lock`: pipenv lockfile (JSON format)
- `environment.yml`: conda environment file (YAML format)

**Version Matching:**
- PEP 440 specifiers: `==`, `>=`, `<=`, `>`, `<`, `!=`, `~=`
- Compound specifiers: `>=1.0,<2.0`
- Poetry caret: `^1.2.3` → `>=1.2.3,<2.0.0`
- Poetry tilde: `~1.2.3` → `>=1.2.3,<1.3.0`

**Key Methods:**
- `detect_projects()`: Finds directories with Python manifests
- `scan_project()`: Scans all Python package manager files
- `_scan_requirements_txt()`: Line-by-line requirements parsing
- `_scan_pyproject_toml()`: TOML parsing for Poetry (requires toml/tomli)
- `_scan_poetry_lock()`: TOML parsing for poetry.lock
- `_scan_pipfile()`: TOML parsing for Pipfile
- `_scan_pipfile_lock()`: JSON parsing for Pipfile.lock
- `_scan_conda_environment()`: YAML parsing for conda (requires PyYAML)
- `_get_matching_pep440_versions()`: PEP 440 compliance checking

## CSV Threat Database

### Format

**Current format (multi-ecosystem):**
```csv
ecosystem,name,version
npm,left-pad,1.3.0
npm,@accordproject/concerto-linter,3.24.1
maven,org.apache.logging.log4j:log4j-core,2.14.1
pip,requests,2.8.1
```

**Legacy format (npm-only, still supported):**
```csv
Package Name,Version
left-pad,1.3.0
@accordproject/concerto-linter,3.24.1
```

### Package Naming Conventions

- **npm**: Package name as-is (supports scoped packages with @)
- **maven**: `groupId:artifactId` format (e.g., `org.springframework:spring-core`)
- **pip**: Package name in lowercase (PyPI convention)

### Current Database Stats

- **Total**: 802 packages, 1,126 versions
- **npm**: 789 packages, 1,055 versions
- **maven**: 4 packages, 35 versions (Log4j, Spring, Jackson, Commons Collections)
- **pip**: 9 packages, 36 versions (requests, Django, Flask, PyYAML, etc.)

## Dependencies

### Core Dependencies (required)
- `click>=8.1`: CLI framework
- `semantic_version>=2.10`: npm semver range parsing

### Optional Dependencies

Install extras for specific ecosystems:
```bash
pip install -e ".[pnpm]"      # PyYAML for pnpm-lock.yaml
pip install -e ".[java]"       # lxml for Maven pom.xml
pip install -e ".[python]"     # toml, packaging for Python
pip install -e ".[all]"        # All optional dependencies
```

**pnpm**: `pyyaml>=6.0` (for pnpm-lock.yaml and conda environment.yml)
**java**: `lxml>=4.9` (for advanced Maven pom.xml features, optional)
**python**: `toml>=0.10`, `packaging>=21.0` (for Poetry and Pipenv)

The adapters gracefully handle missing optional dependencies with warnings.

## Output Format

### Console Output

Findings are grouped by ecosystem and type:
1. **MANIFEST FILES**: Declared dependencies with vulnerable versions/ranges
2. **LOCK FILES**: Exact resolved versions from lockfiles
3. **INSTALLED PACKAGES**: Actually installed packages (npm only)

Each finding includes:
- File path
- Package name and version
- Version specification (for manifests)
- Match type (exact or range)
- Remediation suggestions (upgrade strategy, suggested version)

### JSON Output

Structured report with ecosystem sections:
```json
{
  "total_findings": 31,
  "ecosystems": ["maven", "npm", "pip"],
  "summary": {
    "maven": {"total": 10, "manifest": 10, "lockfile": 0, "unique_packages": 4},
    "npm": {"total": 6, "manifest": 2, "lockfile": 4, "unique_packages": 4},
    "pip": {"total": 15, "manifest": 15, "lockfile": 0, "unique_packages": 9}
  },
  "findings": [...]
}
```

## Docker Deployment

**Image Details:**
- Base: `python:3.11-slim` (~150MB final size)
- User: Non-root `scanner:scanner`
- Entrypoint: `hulud-scan` CLI
- Working directory: `/workspace`
- Threat database: Baked into `/app/sha1-Hulud.csv`

**Dependencies Included:**
- Core: click, semantic_version
- Optional: pyyaml, toml (for full ecosystem support)

**Auto-detection:**
- Automatically detects ecosystems in mounted workspace
- Scans npm, Maven/Gradle, and Python projects
- Generates unified report

**Volume Mounts:**
- `/workspace`: Mount your project here
- Reports saved to `/workspace/hulud_scan_report.json`

**Example Workflows:**

Scan a polyglot monorepo:
```bash
docker run --rm -v "$(pwd):/workspace" hulud-scan
# Auto-detects all ecosystems, reports combined findings
```

CI/CD integration:
```bash
docker run --rm -v "$(pwd):/workspace" hulud-scan --no-save > /dev/null
# Exit code: 0 = clean, 1 = threats found
```

Custom threat database:
```bash
docker run --rm \
  -v "$(pwd):/workspace" \
  -v "$(pwd)/custom-threats.csv:/app/sha1-Hulud.csv" \
  hulud-scan
```

## Test Fixtures

The repository includes test fixtures for all supported ecosystems:

- `examples/test-package/`: npm project with vulnerable packages
- `examples/test-maven/`: Maven pom.xml with vulnerable Java dependencies
- `examples/test-gradle/`: Gradle build.gradle with vulnerable Java dependencies
- `examples/test-python/`: Python project with requirements.txt, pyproject.toml, and Pipfile

Run tests:
```bash
hulud-scan --dir examples --no-save
# Should detect 31 total findings across all ecosystems
```

## Adding New Ecosystems

To add support for a new ecosystem (e.g., Ruby/gem, Rust/cargo):

1. Create adapter: `src/hulud_scan/adapters/new_adapter.py`
2. Inherit from `EcosystemAdapter`
3. Implement required methods:
   - `_get_ecosystem_name()`: Return ecosystem identifier
   - `get_manifest_files()`: List of manifest filenames
   - `get_lockfile_names()`: List of lockfile filenames
   - `detect_projects()`: Find project directories
   - `scan_project()`: Scan manifests, lockfiles, installed packages
4. Register in `adapters/__init__.py`: `ADAPTER_REGISTRY['ecosystem'] = NewAdapter`
5. Add ecosystem to auto-detection in `cli.py`
6. Add test fixtures in `examples/test-ecosystem/`
7. Add sample threats to `sha1-Hulud.csv`

The architecture requires no changes to core components.

## Performance Considerations

- **Lazy Loading**: Only loads adapters for detected ecosystems
- **Skip Directories**: Automatically skips node_modules, .git, venv, build, etc.
- **Streaming**: Parses large files line-by-line where possible
- **No Execution**: Parses configuration files only, never executes package managers
- **Caching**: Single CSV load shared across all adapters

## Security Considerations

- **Sandboxed**: Only reads files, never executes commands
- **Non-root**: Docker runs as unprivileged user
- **Path Validation**: Stays within scan directory
- **No Network**: No external API calls or downloads
- **Static Analysis**: Threat detection is purely static file parsing
