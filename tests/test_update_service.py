"""
Unit tests for update_service according to tim-update skill.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.update_service import is_newer_version


def test_is_newer_version():
    # Newer versions
    assert is_newer_version("1.4.1", "1.4.0") is True
    assert is_newer_version("1.5.0", "1.4.0") is True
    assert is_newer_version("2.0.0", "1.4.0") is True
    assert is_newer_version("v1.4.1", "1.4.0") is True
    assert is_newer_version("1.4.1", "v1.4.0") is True
    assert is_newer_version("1.4.0.1", "1.4.0") is True
    assert is_newer_version("1.4.0-rc1", "1.3.9") is True

    # Same or older versions
    assert is_newer_version("1.4.0", "1.4.0") is False
    assert is_newer_version("1.3.9", "1.4.0") is False
    assert is_newer_version("1.3", "1.4.0") is False
    assert is_newer_version("0.9.9", "1.4.0") is False
    assert is_newer_version("v1.4.0", "1.4.0") is False

    print("All is_newer_version tests passed successfully!")


if __name__ == "__main__":
    test_is_newer_version()
