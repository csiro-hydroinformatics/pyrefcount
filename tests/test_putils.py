import os
from re import sub
import sys
import pytest
from refcount.putils import build_new_path_env, find_full_path, library_short_filename, augment_path_env

pkg_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, pkg_dir)
if sys.platform == "win32":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/x64/Debug")
elif sys.platform == "linux":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/build")
elif sys.platform == "darwin":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/build")
else:
    raise RuntimeError(f"Platform {sys.platform} is not yet supported")


def test_library_short_filename() -> None:
    fname = library_short_filename("test_native_library")
    if sys.platform == "win32":
        assert fname == "test_native_library.dll"
    elif sys.platform == "linux":
        assert fname == "libtest_native_library.so"
    elif sys.platform == "darwin":
        assert fname == "libtest_native_library.dylib"
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
    elif sys.platform == "darwin":
        # /usr/lib/libSystem.dylib ?
        assert find_full_path('System').endswith('libSystem.dylib')
        assert find_full_path('abcdefabcdefabcdef') is None
    else:
        raise RuntimeError(f"Platform {sys.platform} is not yet supported")


def test_library_short_filename():
    assert library_short_filename("Blah", "linux") == "libBlah.so"
    assert library_short_filename("Blah", "win32") == "Blah.dll"
    assert library_short_filename("Blah", "darwin") == "libBlah.dylib"
    with pytest.raises(NotImplementedError):
        _ = library_short_filename("Blah", "unsupported_platform")


def test_prepend_path_env():
    from pathlib import Path
    # user_dir = os.path.expanduser("~")

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp = Path(tmpdirname)
        subfolder = "64" # a hack to be sure the "sub"folder does indeed exist...
        p_1, p_2 = (str(tmp /  "path"), str(tmp/ "more"/ "path"))
        valid_subfolder = tmp / "path" / subfolder
        valid_subfolder.mkdir(parents=True, exist_ok=True)
        new_path = augment_path_env(added_paths = p_1, subfolder = subfolder, to_env = "PATH", prepend=True)
        assert new_path.startswith(os.path.join(p_1, subfolder))
        # and if both, only the one that worked is added
        p = [p_1, p_2]
        new_path = augment_path_env(added_paths = p, subfolder = subfolder, to_env = "PATH", prepend=True)
        assert new_path.startswith(os.path.join(p_1, subfolder))
        assert new_path.find(os.path.join("more", "path")) == -1


def test_build_new_path_env():
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp = Path(tmpdirname)
        subfolder = "64" # a hack to be sure the "sub"folder does indeed exist...
        p_1 = str(tmp /  "path")
        valid_subfolder = tmp / "path" / subfolder
        valid_subfolder.mkdir(parents=True, exist_ok=True)
        os.environ['TEST_PATH_ENV'] = p_1
        # s = build_new_path_env(from_env='TEST_PATH_ENV', to_env='PATH', platform='win32')
        # expected = str(tmp / "path" / subfolder)
        # assert s.endswith(expected)
        s = build_new_path_env(from_env='TEST_PATH_ENV', to_env='PATH', platform=sys.platform)
        if sys.platform == "win32":
            expected = str(tmp / "path" / subfolder)
        else:
            expected = str(tmp / "path")
        assert s.endswith(expected)

def test_new_path_env_warning_msg():
    # unit test for issue #16
    path = os.environ.get('PATH', None)
    assert path is not None
    new_path = build_new_path_env(from_env='UNLIKELY_TEST_PATH_ENV', to_env='PATH', platform=sys.platform)
    assert new_path == path

if __name__ == "__main__":
    test_build_new_path_env()
    test_new_path_env_warning_msg()
