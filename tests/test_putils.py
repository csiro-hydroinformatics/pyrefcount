import os
import sys
import pytest
from refcount.putils import find_full_path, library_short_filename

pkg_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, pkg_dir)
if sys.platform == "win32":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/x64/Debug")
elif sys.platform == "linux":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/build")
else:
    raise RuntimeError(f"Platform {sys.platform} is not yet supported")


def test_library_short_filename():
    fname = library_short_filename("test_native_library")
    if sys.platform == "win32":
        assert fname == "test_native_library"
    elif sys.platform == "linux":
        assert fname == "libtest_native_library.so"
    else:
        raise RuntimeError(f"Platform {sys.platform} is not yet supported")

    with pytest.raises(ValueError):
        _ = library_short_filename(None)


def test_find_full_path():
    assert find_full_path(None) is None
    if sys.platform == "win32":
        assert find_full_path('kernel32').endswith('kernel32.dll')
    elif sys.platform == "linux":
        assert find_full_path('c') == 'libc.so.6'
        assert find_full_path('abcdefabcdefabcdef') is None
    else:
        raise RuntimeError(f"Platform {sys.platform} is not yet supported")

