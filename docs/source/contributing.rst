Contributing
============

We welcome contributions to package-scan! This guide will help you get started.

Development Setup
-----------------

1. Fork the repository on GitHub

2. Clone your fork::

    git clone https://github.com/YOUR_USERNAME/package-scan.git
    cd package-scan

3. Create a virtual environment::

    python3 -m venv venv
    source venv/bin/activate

4. Install in development mode::

    pip install -e ".[dev]"

This installs all dependencies including testing and documentation tools.

Running Tests
-------------

Run all tests::

    pytest

Run specific test file::

    pytest tests/test_npm_adapter.py

Run with coverage::

    pytest --cov=package_scan --cov-report=html

View coverage report::

    open htmlcov/index.html

Code Style
----------

We follow standard Python conventions:

* PEP 8 for code style
* Type hints where appropriate
* Docstrings for public APIs
* Clear, descriptive variable names

Testing Guidelines
------------------

All new features and bug fixes should include tests:

**Unit Tests**
   Test individual functions and classes in isolation

**Integration Tests**
   Test adapter scanning with real file fixtures

**Test Fixtures**
   Use ``pytest`` fixtures for reusable test data

**Example Test**::

    def test_scan_package_json(temp_project_dir, threat_db):
        """Test scanning package.json with vulnerable package."""
        adapter = NpmAdapter(threat_db)

        # Create test file
        package_json = os.path.join(temp_project_dir, 'package.json')
        with open(package_json, 'w') as f:
            json.dump({'dependencies': {'left-pad': '1.3.0'}}, f)

        # Run scan
        findings = adapter.scan_project(temp_project_dir)

        # Assert results
        assert len(findings) == 1
        assert findings[0].package_name == 'left-pad'

Adding New Adapters
-------------------

To add support for a new ecosystem:

1. **Create Adapter File**

   ``src/package_scan/adapters/new_adapter.py``

2. **Implement Interface**

   Inherit from ``EcosystemAdapter`` and implement required methods

3. **Register Adapter**

   Add to ``ADAPTER_REGISTRY`` in ``adapters/__init__.py``

4. **Add Tests**

   Create ``tests/test_new_adapter.py`` with comprehensive tests

5. **Add Fixtures**

   Create ``examples/test-new/`` with sample project files

6. **Update Documentation**

   Add to ecosystem list and architecture docs

See :doc:`architecture` for detailed implementation guide.

Adding New Threats
------------------

To add a new threat database:

1. **Create CSV File**

   ``threats/my-threat.csv``

2. **Use Standard Format**::

    ecosystem,name,version
    npm,package-name,1.0.0
    maven,group.id:artifact-id,2.0.0
    pip,python-package,3.0.0

3. **Test Loading**::

    ptat scan --threat my-threat

4. **Document Threat**

   Add description to README or threat-specific documentation

Documentation
-------------

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

Build HTML documentation::

    cd docs
    make html
    open build/html/index.html

Build for other formats::

    make latexpdf  # PDF via LaTeX
    make epub      # EPUB format

Documentation is written in reStructuredText (RST) and built with Sphinx.

Writing Documentation
~~~~~~~~~~~~~~~~~~~~~

* Use clear, concise language
* Include code examples
* Add cross-references to related sections
* Update API docs when changing function signatures

Pull Request Process
--------------------

1. **Create Feature Branch**::

    git checkout -b feature/my-new-feature

2. **Make Changes**

   * Write code
   * Add tests
   * Update documentation

3. **Run Tests**::

    pytest

4. **Commit Changes**::

    git add .
    git commit -m "Add feature: description"

5. **Push to Fork**::

    git push origin feature/my-new-feature

6. **Open Pull Request**

   * Go to GitHub repository
   * Click "New Pull Request"
   * Describe changes and motivation
   * Reference any related issues

7. **Code Review**

   * Address reviewer feedback
   * Update PR as needed
   * Ensure CI passes

8. **Merge**

   Once approved, maintainers will merge your PR

Commit Message Guidelines
-------------------------

* Use present tense ("Add feature" not "Added feature")
* Use imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit first line to 72 characters
* Reference issues and PRs liberally

**Examples:**

* ``fix: Handle empty package.json files``
* ``feat: Add support for Cargo/Rust ecosystem``
* ``docs: Update installation instructions``
* ``test: Add tests for version range matching``

Bug Reports
-----------

When reporting bugs, please include:

* Package-scan version (``ptat --version``)
* Python version (``python --version``)
* Operating system
* Steps to reproduce
* Expected vs actual behavior
* Relevant error messages or logs
* Sample files if possible

Feature Requests
----------------

When requesting features:

* Describe the use case
* Explain why existing features don't solve the problem
* Provide examples of how it would work
* Consider implementation complexity

Code of Conduct
---------------

This project follows the Contributor Covenant Code of Conduct. Be respectful and inclusive in all interactions.

See CODE_OF_CONDUCT.md for full details.

Getting Help
------------

* Check documentation at https://package-scan.readthedocs.io
* Search existing issues on GitHub
* Open a new issue with the "question" label
* Join discussions in GitHub Discussions

License
-------

By contributing, you agree that your contributions will be licensed under the MIT License.
