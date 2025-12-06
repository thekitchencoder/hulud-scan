Usage
=====

Basic Usage
-----------

Scan Current Directory
~~~~~~~~~~~~~~~~~~~~~~

Scan the current directory for all threats::

    ptat scan

Scan Specific Directory
~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --dir /path/to/project

Threat Selection
----------------

Scan for Specific Threat
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --threat sha1-Hulud

Scan for Multiple Threats
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --threat sha1-Hulud --threat custom-threat

Use Custom CSV File
~~~~~~~~~~~~~~~~~~~

::

    ptat scan --csv /path/to/custom-threats.csv

Ecosystem Selection
-------------------

Scan Specific Ecosystem
~~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --ecosystem npm        # npm only
    ptat scan --ecosystem maven      # Maven/Gradle only
    ptat scan --ecosystem pip        # Python only

Scan Multiple Ecosystems
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --ecosystem npm,maven,pip

List Available Ecosystems
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --list-ecosystems

Output Options
--------------

Custom Output File
~~~~~~~~~~~~~~~~~~

::

    ptat scan --output my_report.json

Disable JSON Report
~~~~~~~~~~~~~~~~~~~

::

    ptat scan --no-save


Threat Database Management
---------------------------

View Threat Database
~~~~~~~~~~~~~~~~~~~~

Display metadata and affected packages::

    ptat db info                                    # Summary + packages (all threats)
    ptat db info --threat sha1-Hulud                # Specific threat
    ptat db info --summary                          # Summary only
    ptat db info --packages                         # Packages only

Export Threat Database
~~~~~~~~~~~~~~~~~~~~~~

Export to CSV format::

    ptat db info --csv > threats.csv                # Full database
    ptat db info --packages --csv                   # CSV data only
    ptat db info --threat sha1-Hulud --packages --csv > hulud.csv  # Specific threat

Validate Threat CSV
~~~~~~~~~~~~~~~~~~~

Validate threat database format::

    ptat db validate --file /path/to/threats.csv
    ptat db validate --file threats.csv --strict    # Strict mode
    ptat db validate --file threats.csv --verbose   # Verbose output

Docker Usage
------------

Basic Docker Scan
~~~~~~~~~~~~~~~~~

::

    docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest

Scan for Specific Threat
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest scan --threat sha1-Hulud

Custom Threat Database
~~~~~~~~~~~~~~~~~~~~~~

::

    docker run --rm \
      -v "$(pwd):/workspace" \
      -v "$(pwd)/custom.csv:/app/custom.csv" \
      kitchencoder/package-scan:latest scan --csv /app/custom.csv

Save Report to Host
~~~~~~~~~~~~~~~~~~~

::

    docker run --rm -v "$(pwd):/workspace" kitchencoder/package-scan:latest scan --output scan_results.json

The report will be saved to ``./scan_results.json`` on your host machine.

Exit Codes
~~~~~~~~~~

* **0**: No threats found
* **1**: Threats found
* **2**: Error occurred

Common Use Cases
----------------

CI/CD Integration
~~~~~~~~~~~~~~~~~

GitHub Actions example::

    - name: Scan for compromised packages
      run: |
        pip install package-scan
        ptat scan --no-save || exit 1

The ``--no-save`` flag skips writing the JSON report, and the command exits with code 1 if threats are found.

Scan Monorepo
~~~~~~~~~~~~~

::

    ptat scan --dir /path/to/monorepo

The scanner will automatically detect and scan all sub-projects.

Audit Specific Dependency File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --dir /path/to/directory --ecosystem npm

Generate Audit Report
~~~~~~~~~~~~~~~~~~~~~

::

    ptat scan --output audit-$(date +%Y%m%d).json

Troubleshooting
---------------

No Findings When Expected
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Check that threat database includes the package::

    ptat db info --packages | grep package-name

2. Verify ecosystem is being scanned::

    ptat scan --list-ecosystems

3. Check version matching is correct

False Positives
~~~~~~~~~~~~~~~

If you believe a finding is incorrect:

1. Check the package version in your manifest/lockfile
2. Verify the threat database has the correct version
3. Review version range matching behavior

Performance Issues
~~~~~~~~~~~~~~~~~~

For large monorepos:

1. Scan specific ecosystems: ``--ecosystem npm``
2. Scan specific directories
3. Use Docker for isolated environment

Output Format
-------------

Console Output
~~~~~~~~~~~~~~

The console output groups findings by ecosystem and type:

* **MANIFEST FILES**: Dependencies with vulnerable version ranges
* **LOCK FILES**: Exact resolved versions from lockfiles
* **INSTALLED PACKAGES**: Actually installed packages (npm only)

Each finding includes:
* File path
* Package name and version
* Version specification (for manifests)
* Match type (exact or range)

JSON Output
~~~~~~~~~~~

The JSON report includes::

    {
      "total_findings": 10,
      "threats": ["sha1-Hulud"],
      "ecosystems": ["npm", "maven", "pip"],
      "summary": {
        "npm": {
          "total": 5,
          "manifest": 2,
          "lockfile": 3,
          "unique_packages": 4
        },
        ...
      },
      "findings": [...]
    }

Each finding contains:
* ``ecosystem``: Package ecosystem
* ``finding_type``: manifest, lockfile, or installed
* ``file_path``: Path to file where found
* ``package_name``: Name of package
* ``version``: Compromised version
* ``match_type``: exact or range
* ``declared_spec``: Version specification (for ranges)
