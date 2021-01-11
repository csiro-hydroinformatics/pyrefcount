import os
import sys
from glob import glob

from ctypes.util import find_library as ctypes_find_library
from typing import List, Union

'''This module will host features similar to https://github.com/rdotnet/dynamic-interop-dll/blob/master/DynamicInterop/PlatformUtility.cs
'''

def library_short_filename(library_name:str) -> str:
    """Based on the library name, return the platform-specific expected library short file name

    Args:
        library_name (str): name of the library, for instance 'R' for 'libR.so'

    Raises:
        Exception: invalid argument

    Returns:
        str: expected short file name for the library, for this platform
    """    
    if library_name is None:
        raise Exception("library_name cannot be None")
    else:
        if(sys.platform == 'win32'):
            return '{}.dll'.format(library_name)
        else:
            return 'lib{}.so'.format(library_name)

def find_full_path(name, dir_path = None):
    """Wrapper around ctypes.util.find_library 
    May need to work around  https://bugs.python.org/issue19317
    """
    libpath = None
    if name is not None:
        libname = library_short_filename(name)
        prefixed_lib_pat = os.path.join(sys.prefix, 'lib*', libname)
        prefixed_libs = glob(prefixed_lib_pat)
        if prefixed_libs:
            libpath = prefixed_libs[0]
    if not libpath:
        libpath = ctypes_find_library(name)
    if libpath is None:
        libpath = name
    return libpath

def prepend_path_env (added_paths:Union[str,List[str]], subfolder:str=None, to_env:str='PATH') -> str:
    """Build a new list of directory paths, prepending prior to an existing env var with paths.

    Args:
        added_paths (Union[str,List[str]]): paths prepended
        subfolder (str, optional): Optional subfolder name to append to each in path prepended. Useful for 64/32 bits variations. Defaults to None.
        to_env (str, optional): Environment variable with existing Paths to start with. Defaults to 'PATH'.

    Returns:
        str: Content (set of paths), typically for a updating/setting an environment variable
    """    
    path_sep = os.path_sep
    if isinstance(added_paths, str):
        added_paths = [added_paths]
    prior_path_env = os.environ.get(to_env)
    if prior_path_env is not None:
        prior_paths = prior_path_env.split(path_sep)
    else:
        prior_paths = []
    if subfolder is not None:
        added_paths = [os.path.join(x,subfolder) for x in added_paths]
    added_paths = [x for x in added_paths if os.path.exists(x)]
    new_paths = prior_paths + added_paths
    # TODO: check for duplicate folders, perhaps.
    new_env_val = path_sep.join(new_paths)
    return new_env_val

