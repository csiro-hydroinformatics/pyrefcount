"""Add tests for boilerplate functions, to isolate relatively "trivial", awkward unit tests done to increase coverage."""

import refcount


# https://discuss.python.org/t/please-make-package-version-go-away/58501
# def test_has_version() -> None:
#     """Check that the package has an `__version__` attribute."""
#     assert refcount.__version__ is not None
#     assert refcount.__version__ != ""


def test_nativehandle() -> None:
    """test_nativehandle."""
    import pytest

    from refcount.base import NativeHandle

    rc = NativeHandle()
    with pytest.raises(NotImplementedError):
        rc._is_valid_handle(None)
    with pytest.raises(NotImplementedError):
        rc._is_valid_handle(None)
