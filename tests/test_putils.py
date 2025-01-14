import os
import sys

import pytest

from refcount.putils import augment_path_env, build_new_path_env, find_full_path, library_short_filename

pkg_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, pkg_dir)
if sys.platform == "win32":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/x64/Debug")
elif sys.platform == "linux" or sys.platform == "darwin":
    dir_path = os.path.join(pkg_dir, "tests/test_native_library/build")
else:
    raise RuntimeError(f"Platform {sys.platform} is not yet supported")


def test_library_short_filename_platform() -> None:
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
        assert find_full_path("kernel32").endswith("kernel32.dll")
    elif sys.platform == "linux":
        assert find_full_path("c") == "libc.so.6"
        assert find_full_path("abcdefabcdefabcdef") is None
        # below was trying to activate one of the branches in the code to increase coverage
        # worked on my machine, but not on the CI (ubuntu-latest) returning 'libffi.so.8'
        # I think libffilso is what is under cffi, and would be installed in the conda/venv environment. TBC.
        # assert find_full_path('ffi').endswith('lib/libffi.so')
    elif sys.platform == "darwin":
        # /usr/lib/libSystem.dylib ?
        assert find_full_path("System").endswith("libSystem.dylib")
        assert find_full_path("abcdefabcdefabcdef") is None
    else:
        raise RuntimeError(f"Platform {sys.platform} is not yet supported")


def test_library_short_filename():
    assert library_short_filename("Blah", "linux") == "libBlah.so"
    assert library_short_filename("Blah", "win32") == "Blah.dll"
    assert library_short_filename("Blah", "darwin") == "libBlah.dylib"
    with pytest.raises(NotImplementedError):
        _ = library_short_filename("Blah", "unsupported_platform")

    with pytest.raises(ValueError):
        _ = library_short_filename(None, "linux")


def test_prepend_path_env():
    # user_dir = os.path.expanduser("~")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp = Path(tmpdirname)
        subfolder = "64"  # a hack to be sure the "sub"folder does indeed exist...
        p_1, p_2 = (str(tmp / "path"), str(tmp / "nonexisting" / "path"))
        valid_subfolder = tmp / "path" / subfolder
        valid_subfolder.mkdir(parents=True, exist_ok=True)
        new_path = augment_path_env(added_paths=p_1, subfolder=subfolder, to_env="PATH", prepend=True)
        assert new_path.startswith(os.path.join(p_1, subfolder))
        # and if both, only the one that worked is added
        p = [p_1, p_2]
        new_path = augment_path_env(added_paths=p, subfolder=subfolder, to_env="PATH", prepend=True)
        assert new_path.startswith(os.path.join(p_1, subfolder))
        assert new_path.find(os.path.join("nonexisting", "path")) == -1

        # UT coverage Cover the case if there is no prior environment variable
        new_path = augment_path_env(added_paths=p, subfolder=subfolder, to_env="ENV_NOT_ALREADY", prepend=False)
        assert new_path.startswith(os.path.join(p_1, subfolder))
        assert new_path.find(os.path.join("nonexisting", "path")) == -1

        # UT coverage Cover the case if there is no prior environment variable,
        # and there is no subfolder
        new_path = augment_path_env(added_paths=p, subfolder="", to_env="ENV_NOT_ALREADY", prepend=False)
        assert new_path.startswith(p_1)
        assert new_path.find(os.path.join("nonexisting", "path")) == -1


def test_win_architecture():
    # for the sake of UT coverage:
    from refcount.putils import _win_architecture

    warch = _win_architecture()
    if sys.platform == "win32":
        assert warch == "64" or warch == "32"
    else:
        assert warch == ""


def test_build_new_path_env():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp = Path(tmpdirname)
        subfolder = "64"  # a hack to be sure the "sub"folder does indeed exist...
        p_1 = str(tmp / "path")
        valid_subfolder = tmp / "path" / subfolder
        valid_subfolder.mkdir(parents=True, exist_ok=True)
        os.environ["TEST_PATH_ENV"] = p_1
        # s = build_new_path_env(from_env='TEST_PATH_ENV', to_env='PATH', platform='win32')
        # expected = str(tmp / "path" / subfolder)
        # assert s.endswith(expected)
        s = build_new_path_env(from_env="TEST_PATH_ENV", to_env="PATH", platform=sys.platform)
        if sys.platform == "win32":
            expected = str(tmp / "path" / subfolder)
        else:
            expected = str(tmp / "path")
        assert s.endswith(expected)

        ## UT coverage: if the from_env is not in os.environ
        # While hypothetical, we certainly want the target environment variable to be returned to avoid messing up the environment the PATH env var for instance.
        s = build_new_path_env(from_env="INVALID_TEST_PATH_ENV", to_env="PATH", platform=sys.platform)
        assert s == os.environ["PATH"]

        # However if the target environment variable is not in os.environ, we return an empty string; nothing to mess up.
        s = build_new_path_env(from_env="INVALID_TEST_PATH_ENV", to_env="INVALID_PATH", platform=sys.platform)
        assert s == ""


def test_new_path_env_warning_msg():
    # unit test for issue #16
    path = os.environ.get("PATH", None)
    assert path is not None
    new_path = build_new_path_env(from_env="UNLIKELY_TEST_PATH_ENV", to_env="PATH", platform=sys.platform)
    assert new_path == path


if __name__ == "__main__":
    test_build_new_path_env()
