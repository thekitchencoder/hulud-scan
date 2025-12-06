"""Unit tests for ThreatMetadata parsing"""

import os
import tempfile
from pathlib import Path

import pytest

from package_scan.core.threat_metadata import (
    parse_threat_metadata,
    filter_csv_comments,
    RECOMMENDED_FIELDS,
)


@pytest.fixture
def csv_with_full_metadata():
    """Create CSV with complete metadata"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("# Description: Test vulnerability in package XYZ\n")
        f.write("# Source: https://example.com/advisory\n")
        f.write("# Last updated: 2025-12-06 10:00:00 UTC\n")
        f.write("# Severity: high\n")
        f.write("# CVE: CVE-2025-12345\n")
        f.write("ecosystem,name,version\n")
        f.write("npm,test-package,1.0.0\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def csv_with_partial_metadata():
    """Create CSV with partial metadata"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("# Description: Partial metadata test\n")
        f.write("ecosystem,name,version\n")
        f.write("npm,test-package,1.0.0\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def csv_without_metadata():
    """Create CSV without any metadata"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("ecosystem,name,version\n")
        f.write("npm,test-package,1.0.0\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def csv_with_comments_only():
    """Create CSV with comments but no metadata fields"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("# This is just a comment\n")
        f.write("# Another comment without colon\n")
        f.write("ecosystem,name,version\n")
        f.write("npm,test-package,1.0.0\n")
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestThreatMetadataParsing:
    """Test metadata parsing from CSV files"""

    def test_parse_full_metadata(self, csv_with_full_metadata):
        """Test parsing CSV with complete metadata"""
        metadata = parse_threat_metadata(Path(csv_with_full_metadata))

        assert metadata.has_field('Description')
        assert metadata.has_field('Source')
        assert metadata.has_field('Last updated')
        assert metadata.has_field('Severity')
        assert metadata.has_field('CVE')

        assert metadata.get('Description') == 'Test vulnerability in package XYZ'
        assert metadata.get('Source') == 'https://example.com/advisory'
        assert metadata.get('Last updated') == '2025-12-06 10:00:00 UTC'
        assert metadata.get('Severity') == 'high'
        assert metadata.get('CVE') == 'CVE-2025-12345'

    def test_parse_partial_metadata(self, csv_with_partial_metadata):
        """Test parsing CSV with partial metadata"""
        metadata = parse_threat_metadata(Path(csv_with_partial_metadata))

        assert metadata.has_field('Description')
        assert not metadata.has_field('Source')
        assert not metadata.has_field('Last updated')

        assert metadata.get('Description') == 'Partial metadata test'

    def test_parse_without_metadata(self, csv_without_metadata):
        """Test parsing CSV without metadata"""
        metadata = parse_threat_metadata(Path(csv_without_metadata))

        assert len(metadata.metadata) == 0
        assert not metadata.has_field('Description')
        assert not metadata.has_field('Source')

    def test_parse_comments_without_fields(self, csv_with_comments_only):
        """Test parsing CSV with comments but no metadata fields"""
        metadata = parse_threat_metadata(Path(csv_with_comments_only))

        assert len(metadata.metadata) == 0
        assert len(metadata.comment_lines) == 2

    def test_case_insensitive_field_access(self, csv_with_full_metadata):
        """Test that field access is case-insensitive"""
        metadata = parse_threat_metadata(Path(csv_with_full_metadata))

        assert metadata.get('description') == metadata.get('Description')
        assert metadata.get('DESCRIPTION') == metadata.get('Description')
        assert metadata.has_field('description')
        assert metadata.has_field('DESCRIPTION')

    def test_missing_recommended_fields(self, csv_with_partial_metadata):
        """Test detection of missing recommended fields"""
        metadata = parse_threat_metadata(Path(csv_with_partial_metadata))

        missing = metadata.get_missing_recommended_fields()
        assert 'source' in missing
        assert 'last updated' in missing
        assert 'description' not in missing

    def test_is_complete(self, csv_with_full_metadata, csv_with_partial_metadata):
        """Test is_complete method"""
        full_metadata = parse_threat_metadata(Path(csv_with_full_metadata))
        partial_metadata = parse_threat_metadata(Path(csv_with_partial_metadata))

        assert full_metadata.is_complete()
        assert not partial_metadata.is_complete()

    def test_nonexistent_file(self):
        """Test parsing nonexistent file"""
        metadata = parse_threat_metadata(Path('/nonexistent/file.csv'))

        assert len(metadata.metadata) == 0
        assert len(metadata.comment_lines) == 0


class TestFilterCSVComments:
    """Test CSV comment filtering"""

    def test_filter_comment_lines(self):
        """Test filtering comment lines from CSV content"""
        lines = [
            "# Comment 1\n",
            "# Comment 2\n",
            "ecosystem,name,version\n",
            "npm,package1,1.0.0\n",
            "# Mid-file comment (should also be filtered)\n",
            "npm,package2,2.0.0\n",
        ]

        filtered = filter_csv_comments(lines)

        assert len(filtered) == 3
        assert "ecosystem,name,version\n" in filtered
        assert "npm,package1,1.0.0\n" in filtered
        assert "npm,package2,2.0.0\n" in filtered

    def test_filter_empty_lines(self):
        """Test filtering empty lines"""
        lines = [
            "\n",
            "ecosystem,name,version\n",
            "\n",
            "npm,package1,1.0.0\n",
            "\n",
        ]

        filtered = filter_csv_comments(lines)

        assert len(filtered) == 2
        assert filtered[0] == "ecosystem,name,version\n"
        assert filtered[1] == "npm,package1,1.0.0\n"

    def test_filter_mixed_content(self):
        """Test filtering mixed comments and data"""
        lines = [
            "# Description: Test file\n",
            "# Source: test\n",
            "\n",
            "ecosystem,name,version\n",
            "npm,pkg1,1.0.0\n",
            "# Comment in data\n",
            "npm,pkg2,2.0.0\n",
            "\n",
        ]

        filtered = filter_csv_comments(lines)

        assert len(filtered) == 3
        assert all(not line.startswith('#') for line in filtered)
        assert all(line.strip() for line in filtered)  # No empty lines


class TestRealThreatFiles:
    """Test metadata parsing on real threat files"""

    def test_parse_cve_2025_55182(self):
        """Test parsing CVE-2025-55182.csv"""
        cve_file = Path(__file__).parent.parent / 'threats' / 'CVE-2025-55182.csv'

        if not cve_file.exists():
            pytest.skip("CVE-2025-55182.csv not found")

        metadata = parse_threat_metadata(cve_file)

        # Should have all recommended fields
        assert metadata.is_complete()
        assert metadata.has_field('Description')
        assert metadata.has_field('Source')
        assert metadata.has_field('Last updated')

        # Check specific values
        assert 'React Server Components' in metadata.get('Description')
        assert 'react.dev' in metadata.get('Source')

    def test_parse_sha1_hulud(self):
        """Test parsing sha1-Hulud.csv"""
        hulud_file = Path(__file__).parent.parent / 'threats' / 'sha1-Hulud.csv'

        if not hulud_file.exists():
            pytest.skip("sha1-Hulud.csv not found")

        metadata = parse_threat_metadata(hulud_file)

        # Should have all recommended fields
        assert metadata.is_complete()
        assert metadata.has_field('Description')
        assert metadata.has_field('Source')
        assert metadata.has_field('Last updated')

        # Check specific values
        assert 'SHA1-Hulud' in metadata.get('Description')
        assert 'koi.ai' in metadata.get('Source')

    def test_parse_sample_threats(self):
        """Test parsing sample-threats.csv (no metadata)"""
        sample_file = Path(__file__).parent.parent / 'threats' / 'sample-threats.csv'

        if not sample_file.exists():
            pytest.skip("sample-threats.csv not found")

        metadata = parse_threat_metadata(sample_file)

        # Should not be complete (no metadata)
        assert not metadata.is_complete()
        assert len(metadata.metadata) == 0
