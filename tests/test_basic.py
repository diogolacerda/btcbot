"""Basic tests to verify CI pipeline works."""


def test_import_src():
    """Test that src module can be imported."""
    import src

    assert src is not None


def test_python_version():
    """Test that we're running on Python 3.12+."""
    import sys

    assert sys.version_info >= (3, 12)


def test_basic_math():
    """Basic sanity check."""
    assert 1 + 1 == 2
