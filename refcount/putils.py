"""Platform specific helpers to manage locating native dynamic libraries

This module hosts features similar to https://github.com/rdotnet/dynamic-interop-dll/blob/master/DynamicInterop/PlatformUtility.cs

"""

import os
import sys
from glob import glob

from ctypes.util import find_library as ctypes_find_library
from typing import List, Union


def library_short_filename(library_name: str) -> str:
    """Based on the library name, return the platform-specific expected library short file name

    Args:
        library_name (str): name of the library, for instance 'R', which results out of this 
            function  as 'libR.so' on Linux and 'R.dll' on Windows

    Raises:
        Exception: invalid argument

    Returns:
        str: expected short file name for the library, for this platform
    """
    if library_name is None:
        raise Exception("library_name cannot be None")
    else:
        if sys.platform == "win32":
            return "{}.dll".format(library_name)
        else:
            return "lib{}.so".format(library_name)

    """Wrapper around ctypes.util.find_library
    May need to work around  https://bugs.python.org/issue19317
    """

def find_full_path(name: str) -> Union[str, None]:
    """Find the full path of a library in under the python 
        installation directory, or as devised by ctypes.find_library

    Args:
        name (str): Library name, e.g. 'R' for the R programming language.

    Returns:
        Union[str, None]: First suitable library full file name.

    Examples:
        >>> from refcount.putils import *
        >>> find_full_path('gfortran')
        '/home/xxxyyy/anaconda3/envs/wqml/lib/libgfortran.so'
        >>> find_full_path('R')
        'libR.so'
    """    
    full_libpath = None
    if name is None:
        return None
    else:
        lib_short_fname = library_short_filename(name)
        prefixed_lib_pat = os.path.join(sys.prefix, "lib*", lib_short_fname)
        prefixed_libs = glob(prefixed_lib_pat)
        if prefixed_libs:
            full_libpath = prefixed_libs[0]
    if not full_libpath:
        full_libpath = ctypes_find_library(name)
    return full_libpath


def find_full_paths(dll_short_name: str, directories: List[str] = None) -> List[str]:
    """Find the full paths to library files, if they exist

    Args:
        dll_short_name (str): Short file name of the libary to search for, e.g. 'libgfortran.so'
        directories (List[str], optional): directories under which to look for this file. Defaults to None.

    Returns:
        List[str]: zero or more matches, full paths to candidate files
    """    
    if directories is None:
        directories = []
    full_paths = [os.path.join(d, dll_short_name) for d in directories]
    return [x for x in full_paths if os.path.exists(x)]


def find_full_paths_env_var(
    dll_short_name: str, env_var_name: str = "PATH"
) -> List[str]:
    """Find the full paths to library files, if they exist

    Args:
        dll_short_name (str): Short file name of the libary to search for, e.g. 'libgfortran.so'
        env_var_name (str, optional): [description]. Environment variable with paths to search under. Defaults to "PATH".

    Returns:
        List[str]: zero or more matches, full paths to candidate files
    """
    x = os.environ.get(env_var_name)
    if x is not None:
        search_paths = x.split(os.pathsep)
    else:
        search_paths = [""]
    return find_full_paths(dll_short_name, search_paths)


def prepend_path_env(
    added_paths: Union[str, List[str]], subfolder: str = None, to_env: str = "PATH"
) -> str:
    """Build a new list of directory paths, prepending prior to an existing env var with paths.

    Args:
        added_paths (Union[str,List[str]]): paths prepended
        subfolder (str, optional): Optional subfolder name to append to each in path prepended. Useful for 64/32 bits variations. Defaults to None.
        to_env (str, optional): Environment variable with existing Paths to start with. Defaults to 'PATH'.

    Returns:
        str: Content (set of paths), typically for a updating/setting an environment variable
    """
    path_sep = os.pathsep
    if isinstance(added_paths, str):
        added_paths = [added_paths]
    prior_path_env = os.environ.get(to_env)
    if prior_path_env is not None:
        prior_paths = prior_path_env.split(path_sep)
    else:
        prior_paths = []
    if subfolder is not None:
        added_paths = [os.path.join(x, subfolder) for x in added_paths]
    added_paths = [x for x in added_paths if os.path.exists(x)]
    new_paths = prior_paths + added_paths
    # TODO: check for duplicate folders, perhaps.
    new_env_val = path_sep.join(new_paths)
    return new_env_val
