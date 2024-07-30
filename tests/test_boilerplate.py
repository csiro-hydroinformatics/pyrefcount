"""
Add tests for boilerplate functions, to isolate relatively "trivial", awkward unit tests done to increase coverage.
"""

import refcount


def test_has_version() -> None:
    assert refcount.__version__ is not None
    assert refcount.__version__ != ""


def test_nativehandle() -> None:
    from refcount.base import NativeHandle
    import pytest
    rc = NativeHandle()
    with pytest.raises(NotImplementedError):
        rc._is_valid_handle(None)
    with pytest.raises(NotImplementedError):
        rc._is_valid_handle(None)
