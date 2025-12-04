"""Threat database management for multi-ecosystem scanning"""

import csv
import sys
from typing import Dict, Set, Optional
from collections import defaultdict
from pathlib import Path
import click


class ThreatDatabase:
    """
    Manages threat data from CSV file with multi-ecosystem support

    CSV Format (new):
        ecosystem,name,version
        npm,left-pad,1.3.0
        maven,org.apache.logging.log4j:log4j-core,2.14.1
        pip,requests,2.25.1
        gem,strong_migrations,0.7.9

    CSV Format (legacy, backward compatible):
        Package Name,Version
        left-pad,1.3.0
        (defaults to npm ecosystem)
    """

    def __init__(self):
        self.csv_file: Optional[Path] = None
        # Structure: {ecosystem: {package_name: set(versions)}}
        self.threats: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self._is_loaded = False
        self._format_version = None  # 'legacy' or 'multi-ecosystem'

    def load(self, csv_file: str) -> bool:
        """
        Load compromised packages from CSV file

        Args:
            csv_file: Path to CSV file

        Returns:
            True if loaded successfully, False otherwise
        """
        self.csv_file = Path(csv_file)

        if not self.csv_file.exists():
            click.echo(click.style(f"✗ Error: CSV file not found: {csv_file}", fg='red', bold=True), err=True)
            return False

        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                if not headers:
                    click.echo(click.style(f"✗ Error: CSV file has no headers", fg='red', bold=True), err=True)
                    return False

                # Detect format
                if 'ecosystem' in headers and 'name' in headers and 'version' in headers:
                    self._format_version = 'multi-ecosystem'
                    self._load_multi_ecosystem_format(reader)
                elif 'Package Name' in headers and 'Version' in headers:
                    self._format_version = 'legacy'
                    click.echo(click.style(
                        "⚠️  Warning: Using legacy CSV format (Package Name,Version). "
                        "Consider upgrading to multi-ecosystem format (ecosystem,name,version).",
                        fg='yellow'), err=True)
                    self._load_legacy_format(reader)
                else:
                    click.echo(click.style(
                        f"✗ Error: Unrecognized CSV format. "
                        f"Expected headers: 'ecosystem,name,version' or 'Package Name,Version'. "
                        f"Got: {','.join(headers)}",
                        fg='red', bold=True), err=True)
                    return False

            self._is_loaded = True
            return True

        except UnicodeDecodeError as e:
            click.echo(click.style(f"✗ Error: CSV file encoding issue: {e}", fg='red', bold=True), err=True)
            return False
        except Exception as e:
            click.echo(click.style(f"✗ Error loading CSV: {e}", fg='red', bold=True), err=True)
            return False

    def _load_multi_ecosystem_format(self, reader):
        """Load CSV in multi-ecosystem format"""
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
            try:
                ecosystem = row['ecosystem'].strip().lower()
                name = row['name'].strip()
                version = row['version'].strip()

                if not ecosystem or not name or not version:
                    click.echo(click.style(
                        f"⚠️  Warning: Skipping row {row_num} with empty fields: {row}",
                        fg='yellow'), err=True)
                    continue

                self.threats[ecosystem][name].add(version)

            except KeyError as e:
                click.echo(click.style(
                    f"⚠️  Warning: Skipping row {row_num} with missing field {e}: {row}",
                    fg='yellow'), err=True)
                continue

    def _load_legacy_format(self, reader):
        """Load CSV in legacy npm-only format, defaulting to npm ecosystem"""
        for row_num, row in enumerate(reader, start=2):
            try:
                name = row['Package Name'].strip()
                version = row['Version'].strip()

                if not name or not version:
                    click.echo(click.style(
                        f"⚠️  Warning: Skipping row {row_num} with empty fields: {row}",
                        fg='yellow'), err=True)
                    continue

                # Default to npm ecosystem for backward compatibility
                self.threats['npm'][name].add(version)

            except KeyError as e:
                click.echo(click.style(
                    f"⚠️  Warning: Skipping row {row_num} with missing field {e}: {row}",
                    fg='yellow'), err=True)
                continue

    def get_compromised_versions(self, ecosystem: str, package_name: str) -> Set[str]:
        """
        Get all compromised versions for a specific package in an ecosystem

        Args:
            ecosystem: Ecosystem name (npm, maven, pip, gem, etc.)
            package_name: Package identifier

        Returns:
            Set of compromised version strings
        """
        if not self._is_loaded:
            return set()

        ecosystem = ecosystem.lower()
        return self.threats.get(ecosystem, {}).get(package_name, set())

    def is_compromised(self, ecosystem: str, package_name: str, version: str) -> bool:
        """
        Check if a specific package version is compromised

        Args:
            ecosystem: Ecosystem name
            package_name: Package identifier
            version: Version string

        Returns:
            True if compromised, False otherwise
        """
        compromised_versions = self.get_compromised_versions(ecosystem, package_name)
        return version in compromised_versions

    def get_all_packages(self, ecosystem: Optional[str] = None) -> Dict[str, Set[str]]:
        """
        Get all compromised packages, optionally filtered by ecosystem

        Args:
            ecosystem: Optional ecosystem filter

        Returns:
            Dictionary mapping package names to sets of compromised versions
        """
        if not self._is_loaded:
            return {}

        if ecosystem:
            ecosystem = ecosystem.lower()
            return dict(self.threats.get(ecosystem, {}))
        else:
            # Return all ecosystems merged (not recommended, use with caution)
            all_packages = defaultdict(set)
            for eco_threats in self.threats.values():
                for pkg_name, versions in eco_threats.items():
                    all_packages[pkg_name].update(versions)
            return dict(all_packages)

    def get_ecosystems(self) -> Set[str]:
        """
        Get all ecosystems present in the threat database

        Returns:
            Set of ecosystem names
        """
        if not self._is_loaded:
            return set()

        return set(self.threats.keys())

    def get_package_count(self, ecosystem: Optional[str] = None) -> int:
        """
        Get count of unique packages in threat database

        Args:
            ecosystem: Optional ecosystem filter

        Returns:
            Number of unique packages
        """
        if ecosystem:
            ecosystem = ecosystem.lower()
            return len(self.threats.get(ecosystem, {}))
        else:
            # Total across all ecosystems
            return sum(len(packages) for packages in self.threats.values())

    def get_version_count(self, ecosystem: Optional[str] = None) -> int:
        """
        Get count of compromised package versions

        Args:
            ecosystem: Optional ecosystem filter

        Returns:
            Total number of compromised versions
        """
        if ecosystem:
            ecosystem = ecosystem.lower()
            eco_threats = self.threats.get(ecosystem, {})
            return sum(len(versions) for versions in eco_threats.values())
        else:
            # Total across all ecosystems
            total = 0
            for eco_threats in self.threats.values():
                total += sum(len(versions) for versions in eco_threats.values())
            return total

    def print_summary(self):
        """Print a summary of loaded threats"""
        if not self._is_loaded:
            click.echo(click.style("✗ Threat database not loaded", fg='red', bold=True))
            return

        ecosystems = self.get_ecosystems()

        if not ecosystems:
            click.echo(click.style("⚠️  Warning: Threat database is empty", fg='yellow', bold=True))
            return

        total_packages = self.get_package_count()
        total_versions = self.get_version_count()

        click.echo(click.style(f"✓ Loaded threat database: {total_packages} packages, {total_versions} versions", fg='green', bold=True))

        if len(ecosystems) > 1:
            click.echo(click.style(f"  Ecosystems: {', '.join(sorted(ecosystems))}", fg='cyan'))
            for ecosystem in sorted(ecosystems):
                pkg_count = self.get_package_count(ecosystem)
                ver_count = self.get_version_count(ecosystem)
                click.echo(click.style(f"    • {ecosystem}: {pkg_count} packages, {ver_count} versions", fg='cyan', dim=True))
        else:
            # Single ecosystem (likely legacy format)
            ecosystem = list(ecosystems)[0]
            click.echo(click.style(f"  Ecosystem: {ecosystem}", fg='cyan'))
