#!/usr/bin/env python3
"""
Multi-Ecosystem Package Threat Scanner
Scans for compromised packages across npm, Maven/Gradle, pip, and gem ecosystems

CLI usage:
    package-scan --dir /path/to/project --csv /path/to/threats.csv
    package-scan --ecosystem npm,maven
    threat-db validate --file /path/to/threats.csv
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

import click

from package_scan.adapters import get_adapter_class, get_available_ecosystems
from package_scan.adapters.base import ProgressSpinner
from package_scan.core import ThreatDatabase, ReportEngine


def resolve_threats_dir() -> Path:
    """
    Resolve threats directory with smart defaults

    Returns:
        Resolved threats directory path
    """
    # Try multiple default locations for threats directory
    candidates = [
        Path.cwd() / 'threats',      # Current directory
        Path('/app/threats'),         # Docker app directory
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Default to first candidate (for better error message)
    return candidates[0]


def auto_detect_ecosystems(root_dir: Path) -> List[str]:
    """
    Auto-detect which ecosystems are present in the directory

    Args:
        root_dir: Root directory to scan

    Returns:
        List of detected ecosystem names
    """
    detected = set()

    # Mapping of file patterns to ecosystems
    # Note: Both Maven and Gradle use 'maven' ecosystem (Maven Central artifact format)
    indicators = {
        'npm': ['package.json'],
        'maven': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
        'pip': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile'],
        'gem': ['Gemfile'],
    }

    # Walk directory tree looking for indicator files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip common excluded directories
        dirnames[:] = [d for d in dirnames if d not in {
            'node_modules', '.git', 'venv', 'env', '.venv',
            'build', 'dist', 'target', 'vendor', '__pycache__'
        }]

        for ecosystem, patterns in indicators.items():
            if any(pattern in filenames for pattern in patterns):
                detected.add(ecosystem)

        # Early exit if we've found all possible ecosystems
        if len(detected) == len(indicators):
            break

    return sorted(detected)


def filter_available_ecosystems(requested: List[str]) -> List[str]:
    """
    Filter requested ecosystems to only those with implemented adapters

    Args:
        requested: List of requested ecosystem names

    Returns:
        List of available ecosystem names, with warnings for unavailable ones
    """
    available = get_available_ecosystems()
    filtered = []

    for ecosystem in requested:
        if ecosystem in available:
            filtered.append(ecosystem)
        else:
            click.echo(click.style(
                f"⚠️  Warning: {ecosystem} ecosystem requested but adapter not yet implemented. Skipping.",
                fg='yellow'), err=True)
            click.echo(click.style(
                f"   Available: {', '.join(available)}",
                fg='yellow', dim=True), err=True)

    return filtered


@click.command(name="package-scan", help="Multi-ecosystem package threat scanner")
@click.option(
    "--dir",
    "scan_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    default=lambda: os.getcwd(),
    show_default="current working directory",
    help="Root directory to scan recursively",
)
@click.option(
    "--threat",
    "threat_names",
    type=str,
    multiple=True,
    help="Threat name to scan for (repeatable). Example: --threat sha1-Hulud --threat other-threat",
)
@click.option(
    "--csv",
    "csv_file",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=str),
    default=None,
    help="Path to custom CSV file (overrides --threat). For backward compatibility.",
)
@click.option(
    "--ecosystem",
    "ecosystems",
    type=str,
    default=None,
    help="Comma-separated list of ecosystems to scan (e.g., 'npm,maven'). Default: auto-detect",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(writable=True, dir_okay=False, path_type=str),
    default="package_scan_report.json",
    show_default=True,
    help="File to write JSON report",
)
@click.option(
    "--no-save",
    is_flag=True,
    help="Do not write JSON report to disk"
)
@click.option(
    "--list-ecosystems",
    is_flag=True,
    help="List supported ecosystems and exit"
)
def cli(
    scan_dir: str,
    threat_names: tuple,
    csv_file: Optional[str],
    ecosystems: Optional[str],
    output_file: str,
    no_save: bool,
    list_ecosystems: bool
):
    """Multi-ecosystem package threat scanner CLI"""

    # Handle --list-ecosystems
    if list_ecosystems:
        available = get_available_ecosystems()
        click.echo(click.style("=" * 80, fg='cyan', bold=True))
        click.echo(click.style("🌍 SUPPORTED ECOSYSTEMS", fg='cyan', bold=True))
        click.echo(click.style("=" * 80, fg='cyan', bold=True))
        click.echo(f"\n{len(available)} ecosystem(s) currently supported:\n")

        for ecosystem in available:
            adapter_class = get_adapter_class(ecosystem)
            click.echo(f"  • {click.style(ecosystem, fg='green', bold=True)}")

            # Create a dummy instance to get file info
            dummy_db = ThreatDatabase()
            dummy_adapter = adapter_class(dummy_db, Path.cwd(), ProgressSpinner(enabled=False))

            manifests = ', '.join(dummy_adapter.get_manifest_files())
            lockfiles = ', '.join(dummy_adapter.get_lockfile_names())

            click.echo(f"    Manifests: {manifests}")
            click.echo(f"    Lockfiles: {lockfiles}")
            click.echo()

        sys.exit(0)

    # Resolve threats directory
    threats_dir = resolve_threats_dir()

    # Print banner
    click.echo(click.style("=" * 80, fg='cyan', bold=True))
    click.echo(click.style("🛡️  Multi-Ecosystem Package Threat Scanner", fg='cyan', bold=True))
    click.echo(click.style("=" * 80, fg='cyan', bold=True))

    # Validate and resolve scan directory
    scan_dir = os.path.abspath(scan_dir)
    if not os.path.isdir(scan_dir):
        click.echo(click.style(f"✗ Error: Directory not found: {scan_dir}", fg='red', bold=True))
        sys.exit(1)

    click.echo(f"\n{click.style('Scan Directory:', bold=True)} {scan_dir}")
    if csv_file:
        click.echo(f"{click.style('Custom CSV:', bold=True)} {csv_file}")
    elif threat_names:
        click.echo(f"{click.style('Threats:', bold=True)} {', '.join(threat_names)}")
    else:
        click.echo(f"{click.style('Threats Directory:', bold=True)} {threats_dir} (all)")
    click.echo()

    # Load threat database
    threat_db = ThreatDatabase(threats_dir=str(threats_dir))

    # Convert threat_names tuple to list
    threat_list = list(threat_names) if threat_names else None

    if not threat_db.load_threats(threat_names=threat_list, csv_file=csv_file):
        sys.exit(1)

    threat_db.print_summary()

    # Determine which ecosystems to scan
    if ecosystems:
        # User specified ecosystems
        requested_ecosystems = [e.strip().lower() for e in ecosystems.split(',')]
        ecosystems_to_scan = filter_available_ecosystems(requested_ecosystems)

        if not ecosystems_to_scan:
            click.echo(click.style(
                "✗ Error: No valid ecosystems specified",
                fg='red', bold=True))
            click.echo(f"   Available: {', '.join(get_available_ecosystems())}")
            sys.exit(1)

        click.echo(click.style(
            f"🎯 Scanning ecosystems: {', '.join(ecosystems_to_scan)}",
            fg='cyan', bold=True))

    else:
        # Auto-detect ecosystems
        click.echo(click.style("🔍 Auto-detecting ecosystems...", fg='cyan'))
        detected = auto_detect_ecosystems(Path(scan_dir))

        if not detected:
            click.echo(click.style(
                "⚠️  Warning: No recognizable project files found. "
                "Try specifying --ecosystem explicitly.",
                fg='yellow', bold=True))
            sys.exit(0)

        # Filter to only implemented adapters
        ecosystems_to_scan = filter_available_ecosystems(detected)

        if not ecosystems_to_scan:
            click.echo(click.style(
                f"⚠️  Warning: Detected ecosystems {', '.join(detected)} "
                f"but no adapters implemented yet.",
                fg='yellow', bold=True))
            sys.exit(0)

        click.echo(click.style(
            f"✓ Detected: {', '.join(detected)}",
            fg='green'))

        if set(detected) != set(ecosystems_to_scan):
            not_available = set(detected) - set(ecosystems_to_scan)
            click.echo(click.style(
                f"   Note: {', '.join(not_available)} detected but not yet supported",
                fg='yellow', dim=True))

        click.echo(click.style(
            f"   Scanning: {', '.join(ecosystems_to_scan)}",
            fg='cyan', bold=True))

    # Initialize report engine
    report_engine = ReportEngine(scan_dir=scan_dir)

    # Set threats in report engine
    report_engine.set_threats(threat_db.get_loaded_threats())

    # Scan each ecosystem
    spinner = ProgressSpinner()

    for ecosystem in ecosystems_to_scan:
        # Check if ecosystem has threats in database
        if ecosystem not in threat_db.get_ecosystems():
            click.echo(click.style(
                f"\n⚠️  Note: No threats for {ecosystem} in database. Skipping.",
                fg='yellow', dim=True))
            continue

        # Get adapter class and instantiate
        adapter_class = get_adapter_class(ecosystem)
        if not adapter_class:
            click.echo(click.style(
                f"⚠️  Warning: Adapter for {ecosystem} not found. Skipping.",
                fg='yellow'), err=True)
            continue

        adapter = adapter_class(threat_db, Path(scan_dir), spinner)

        # Scan all projects for this ecosystem
        findings = adapter.scan_all_projects()
        report_engine.add_findings(findings)

    spinner.clear()

    # Print report
    report_engine.print_report()

    # Save report if requested
    if not no_save:
        absolute_output = os.path.abspath(output_file)
        if report_engine.save_report(absolute_output):
            click.echo(click.style(
                f"✓ Report saved to: {absolute_output}",
                fg='green', bold=True))

    # Exit with non-zero if threats found
    if report_engine.get_findings_count() > 0:
        sys.exit(1)
    else:
        sys.exit(0)


@click.group(name="threat-db", help="Threat database management commands")
def threat_db_cli():
    """Threat database management command group"""
    pass


@threat_db_cli.command(name="info", help="Display threat database information")
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=str),
    help="Path to specific threat CSV file"
)
@click.option(
    "--threat",
    "threat_names",
    multiple=True,
    help="Filter for specific threat(s) by name"
)
@click.option(
    "--summary",
    is_flag=True,
    help="Show metadata and statistics (default)"
)
@click.option(
    "--packages",
    is_flag=True,
    help="List all affected packages"
)
@click.option(
    "--csv",
    "csv_output",
    is_flag=True,
    help="Output in CSV format"
)
def info_threat_db(file_path: str, threat_names: tuple, summary: bool, packages: bool, csv_output: bool):
    """
    Display threat database information

    By default, shows both metadata/statistics and packages.
    Can filter by specific threat or file, and output in different formats.

    Examples:
        threat-db info                                  # Show summary + packages for all threats
        threat-db info --file threats/CVE-2025-55182.csv # Show summary + packages for file
        threat-db info --threat sha1-Hulud              # Show summary + packages for threat
        threat-db info --summary                        # Show only summary
        threat-db info --packages                       # Show only packages
        threat-db info --packages --csv                 # Export packages as CSV
        threat-db info --csv                            # Export both (metadata as # comments)
    """
    from package_scan.core import parse_threat_metadata, ThreatDatabase
    from pathlib import Path

    # Determine what to show: default is BOTH summary and packages
    show_summary = summary or (not summary and not packages)
    show_packages = packages or (not summary and not packages)

    # Handle file-based query (single file)
    if file_path:
        if csv_output:
            # CSV output: metadata as # comments, then raw CSV
            if show_summary:
                metadata = parse_threat_metadata(Path(file_path))
                if metadata.metadata:
                    for key, value in metadata.metadata.items():
                        click.echo(f"# {key}: {value}")
                if show_packages:
                    click.echo("#")  # Blank comment line separator

            if show_packages:
                # Output raw CSV (with headers)
                with open(Path(file_path), 'r', encoding='utf-8-sig') as f:
                    for line in f:
                        stripped = line.strip()
                        # Skip comment lines (they're already output above if needed)
                        if not stripped or stripped.startswith('#'):
                            continue
                        click.echo(line.rstrip())
        else:
            # Formatted output
            metadata = parse_threat_metadata(Path(file_path))
            metadata.compute_stats()

            if show_summary:
                metadata.print_metadata()

            if show_packages:
                if show_summary:
                    click.echo()  # Blank line separator
                _print_packages_from_file(Path(file_path))
        return

    # Handle threat database query (all threats or filtered)
    threats_dir = resolve_threats_dir()
    threat_db = ThreatDatabase(threats_dir=str(threats_dir))
    threat_list = list(threat_names) if threat_names else None

    if not threat_db.load_threats(threat_names=threat_list):
        sys.exit(1)

    if csv_output:
        # CSV output: metadata as # comments, then raw CSV data
        if show_summary:
            for threat_name in threat_db.get_loaded_threats():
                threat_file = threats_dir / f"{threat_name}.csv"
                if threat_file.exists():
                    metadata = parse_threat_metadata(threat_file)
                    click.echo(f"# Threat: {threat_name}")
                    if metadata.metadata:
                        for key, value in metadata.metadata.items():
                            click.echo(f"# {key}: {value}")
                    click.echo("#")  # Blank comment line

        if show_packages:
            # Output CSV data
            click.echo("ecosystem,name,version")
            for ecosystem in sorted(threat_db.get_ecosystems()):
                packages_dict = threat_db.get_all_packages(ecosystem)
                for pkg_name in sorted(packages_dict.keys()):
                    for version in sorted(packages_dict[pkg_name]):
                        click.echo(f"{ecosystem},{pkg_name},{version}")
    else:
        # Formatted output
        if show_summary:
            for threat_name in threat_db.get_loaded_threats():
                threat_file = threats_dir / f"{threat_name}.csv"
                if threat_file.exists():
                    metadata = parse_threat_metadata(threat_file)
                    metadata.compute_stats()
                    metadata.print_metadata()
                    click.echo()

        if show_packages:
            _print_packages_formatted(threat_db)


def _print_packages_from_file(file_path: Path):
    """Print packages from a single threat file in formatted style"""
    import csv
    from package_scan.core.threat_metadata import get_csv_reader_without_comments
    from collections import defaultdict

    ecosystems = defaultdict(lambda: defaultdict(set))

    csv_content = get_csv_reader_without_comments(file_path)
    reader = csv.DictReader(csv_content)

    for row in reader:
        ecosystem = row.get('ecosystem', '').strip().lower()
        name = row.get('name', '').strip()
        version = row.get('version', '').strip()
        if ecosystem and name and version:
            ecosystems[ecosystem][name].add(version)

    click.echo("\n" + click.style("=" * 80, fg='yellow', bold=True))
    click.echo(click.style("⚠️  COMPROMISED PACKAGES", fg='yellow', bold=True))
    click.echo(click.style("=" * 80, fg='yellow', bold=True))
    click.echo(click.style(f"\nFile: {file_path}", fg='cyan', bold=True))

    for ecosystem in sorted(ecosystems.keys()):
        packages = ecosystems[ecosystem]
        total_versions = sum(len(versions) for versions in packages.values())

        click.echo(f"\n{click.style(f'📦 {ecosystem.upper()}:', fg='magenta', bold=True)}")
        click.echo(f"   {len(packages)} unique packages, {total_versions} versions\n")

        for pkg_name in sorted(packages.keys()):
            versions = sorted(packages[pkg_name])
            click.echo(f"  {click.style(pkg_name, fg='red', bold=True)}")
            for ver in versions:
                click.echo(f"    └─ {ver}")

    click.echo(f"\n" + click.style("=" * 80, fg='yellow', bold=True))


def _print_packages_formatted(threat_db):
    """Print packages from threat database in formatted style"""
    click.echo("\n" + click.style("=" * 80, fg='yellow', bold=True))
    click.echo(click.style("⚠️  COMPROMISED PACKAGES IN THREAT DATABASE", fg='yellow', bold=True))
    click.echo(click.style("=" * 80, fg='yellow', bold=True))

    # Show which threats are included
    if threat_db.get_loaded_threats():
        threat_list_str = ', '.join(threat_db.get_loaded_threats())
        click.echo(click.style(f"\n🔎 Threats: {threat_list_str}", fg='cyan', bold=True))

    all_ecosystems = threat_db.get_ecosystems()

    for ecosystem in sorted(all_ecosystems):
        packages = threat_db.get_all_packages(ecosystem)

        click.echo(f"\n{click.style(f'📦 {ecosystem.upper()}:', fg='magenta', bold=True)}")
        click.echo(f"   {len(packages)} unique packages, "
                  f"{threat_db.get_version_count(ecosystem)} versions\n")

        for pkg_name in sorted(packages.keys()):
            versions = sorted(packages[pkg_name])
            click.echo(f"  {click.style(pkg_name, fg='red', bold=True)}")
            for ver in versions:
                click.echo(f"    └─ {ver}")

    click.echo(f"\n" + click.style("=" * 80, fg='yellow', bold=True))


@threat_db_cli.command(name="validate", help="Validate threat CSV file format")
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=str),
    required=True,
    help="Path to threat CSV file to validate"
)
@click.option(
    "--strict",
    is_flag=True,
    help="Strict mode: only allow known ecosystems (npm, maven, pip, gem)"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show all warnings and detailed information"
)
def validate_threat_db(file_path: str, strict: bool, verbose: bool):
    """
    Validate threat database CSV file

    Checks for:
    - Correct headers (ecosystem,name,version or Package Name,Version)
    - Valid field values (non-empty, proper format)
    - Known ecosystems (in strict mode)
    - Duplicate entries
    - Package name format (ecosystem-specific)

    Examples:
        package-scan threat-db validate --file threats/sha1-Hulud.csv
        package-scan threat-db validate --file custom-threats.csv --strict
        package-scan threat-db validate --file threats.csv --verbose
    """
    from package_scan.core import validate_threat_file

    success = validate_threat_file(file_path, strict=strict, verbose=verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    cli()
