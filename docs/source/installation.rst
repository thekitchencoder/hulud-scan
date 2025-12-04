Installation
============

Requirements
------------

* Python 3.8 or higher
* pip package manager

Core Dependencies
~~~~~~~~~~~~~~~~~

* click >= 8.1
* semantic_version >= 2.10

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

For full ecosystem support, install optional dependencies:

* **pnpm support**: pyyaml >= 6.0
* **Java/Maven support**: lxml >= 4.9
* **Python ecosystem support**: toml >= 0.10, packaging >= 21.0

Installation Methods
--------------------

From Source (Development)
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Clone the repository::

    git clone https://github.com/thekitchencoder/package-scan.git
    cd package-scan

2. Create a virtual environment::

    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\\Scripts\\activate

3. Install in editable mode::

    pip install -e .

4. Install with all optional dependencies::

    pip install -e ".[all]"

Or install specific ecosystem support::

    pip install -e ".[pnpm]"      # pnpm support
    pip install -e ".[java]"       # Maven/Gradle support
    pip install -e ".[python]"     # Python ecosystem support

Verify Installation
~~~~~~~~~~~~~~~~~~~

Check that the command is available::

    package-scan --help
    package-scan --list-ecosystems

Using Docker
------------

Pull from Docker Hub
~~~~~~~~~~~~~~~~~~~~

::

    docker pull kitchencoder/package-scan:latest

Or build locally::

    docker build -t package-scan .

Run with Docker
~~~~~~~~~~~~~~~

Scan current directory::

    docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest

Scan for specific threat::

    docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest --threat sha1-Hulud

The Docker image includes all optional dependencies and threat databases.

Development Installation
------------------------

For contributing to package-scan, install development dependencies::

    pip install -e ".[dev]"

This includes:
* pytest for testing
* sphinx for documentation
* sphinx-rtd-theme for documentation theme
* myst-parser for Markdown support

Run tests::

    pytest

Build documentation::

    cd docs
    make html

Upgrading
---------

To upgrade to the latest version::

    cd package-scan
    git pull
    pip install -e ".[all]"

Uninstallation
--------------

To uninstall::

    pip uninstall package-scan

Troubleshooting
---------------

Command not found
~~~~~~~~~~~~~~~~~

If ``package-scan`` is not found:

1. Ensure your virtual environment is activated
2. Verify installation: ``pip list | grep package-scan``
3. Try running with Python module: ``python -m package_scan.cli``

Import Errors
~~~~~~~~~~~~~

If you get import errors for optional dependencies:

* For pnpm support: ``pip install pyyaml``
* For Maven support: ``pip install lxml``
* For Python ecosystem: ``pip install toml packaging``

Or install all at once: ``pip install -e ".[all]"``
