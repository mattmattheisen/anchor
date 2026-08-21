"""
Version contract tests for Anchor.

These tests protect the distinction between Anchor's
codebase release version and its serialized output schema
version.
"""

from engine.package_version import ANCHOR_VERSION
from engine.version import ANCHOR_SCHEMA_VERSION


def test_anchor_package_version():
    assert ANCHOR_VERSION == "1.0.0"


def test_anchor_schema_version():
    assert ANCHOR_SCHEMA_VERSION == "1.0"


def test_package_and_schema_versions_are_distinct():
    assert ANCHOR_VERSION != ANCHOR_SCHEMA_VERSION
