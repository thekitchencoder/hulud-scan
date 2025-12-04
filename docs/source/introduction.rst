Introduction
============

Overview
--------

**package-scan** is a security scanning tool designed to detect compromised packages in your software projects. It scans multiple package ecosystems (npm, Maven, pip) against a database of known compromised packages from supply chain attacks.

The tool helps you identify:

* Packages affected by specific threats (e.g., sha1-Hulud worm)
* Vulnerable versions in your dependencies
* Compromised packages in lockfiles and installed packages
* Security risks across multiple ecosystems

Why package-scan?
-----------------

Supply chain attacks are an increasing threat to software security. Attackers compromise popular packages to distribute malware, steal credentials, or inject backdoors. package-scan helps you:

**Detect Known Threats**
   Scan your projects against databases of known compromised packages

**Multi-Ecosystem Coverage**
   Single tool for JavaScript, Java, and Python projects

**Version Range Analysis**
   Intelligent matching of version ranges (^1.0.0, [5.0,6.0), >=2.0)

**Automated Scanning**
   Integrate into CI/CD pipelines for continuous monitoring

**Detailed Reports**
   JSON reports with file locations and remediation suggestions

Supported Ecosystems
--------------------

npm (JavaScript/Node.js)
~~~~~~~~~~~~~~~~~~~~~~~~

Scans:
* package.json manifests
* package-lock.json (npm)
* yarn.lock (Yarn)
* pnpm-lock.yaml (pnpm)
* node_modules/ installed packages

Maven/Gradle (Java)
~~~~~~~~~~~~~~~~~~~

Scans:
* pom.xml (Maven)
* build.gradle (Gradle Groovy DSL)
* build.gradle.kts (Gradle Kotlin DSL)
* gradle.lockfile (Gradle lockfiles)

pip (Python)
~~~~~~~~~~~~

Scans:
* requirements.txt files
* pyproject.toml (Poetry)
* poetry.lock
* Pipfile (pipenv)
* Pipfile.lock
* environment.yml (conda)

Threat Database
---------------

The tool uses CSV-based threat databases located in the ``threats/`` directory. Each CSV file represents a specific supply chain attack or threat campaign.

**Format**::

   ecosystem,name,version
   npm,left-pad,1.3.0
   maven,org.springframework:spring-core,5.3.0
   pip,requests,2.8.1

**Built-in Threats:**

* **sha1-Hulud.csv**: sha1-Hulud worm (790 packages, 1,056 versions)
* **sample-threats.csv**: Test threats for all ecosystems

You can also provide custom threat databases using the ``--csv`` option.

How It Works
------------

1. **Detection**: Scans directories for package manifests and lockfiles
2. **Parsing**: Extracts package names and versions from various formats
3. **Matching**: Compares against threat database with intelligent version matching
4. **Reporting**: Generates detailed findings with file locations and remediation

The scanner uses ecosystem-specific adapters that understand each package manager's file formats and version semantics.
