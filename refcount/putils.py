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
        ValueError: invalid argument

    Returns:
        str: expected short file name for the library, for this platform
    """
    if library_name is None:
        raise ValueError("library_name cannot be None")
    else:
        if sys.platform == "win32":
            return "{}.dll".format(library_name)
        else:
            return "lib{}.so".format(library_name)

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


# def find_full_paths(dll_short_name: str, directories: List[str] = None) -> List[str]:
#     """Find the full paths to library files, if they exist

#     Args:
#         dll_short_name (str): Short file name of the libary to search for, e.g. 'libgfortran.so'
#         directories (List[str], optional): directories under which to look for this file. Defaults to None.

#     Returns:
#         List[str]: zero or more matches, full paths to candidate files
#     """    
#     if directories is None:
#         directories = []
#     full_paths = [os.path.join(d, dll_short_name) for d in directories]
#     return [x for x in full_paths if os.path.exists(x)]


# def find_full_paths_env_var(
#     dll_short_name: str, env_var_name: str = "PATH"
# ) -> List[str]:
#     """Find the full paths to library files, if they exist

#     Args:
#         dll_short_name (str): Short file name of the libary to search for, e.g. 'libgfortran.so'
#         env_var_name (str, optional): [description]. Environment variable with paths to search under. Defaults to "PATH".

#     Returns:
#         List[str]: zero or more matches, full paths to candidate files
#     """
#     x = os.environ.get(env_var_name)
#     if x is not None:
#         search_paths = x.split(os.pathsep)
#     else:
#         search_paths = [""]
#     return find_full_paths(dll_short_name, search_paths)


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

# TODO: is that of any use still?? refactored out from uchronia and co. , but appears unused.
# def find_first_full_path(native_lib_file_name, readable_lib_name = "native library", env_var_name = ""):
#     if os.path.isabs(native_lib_file_name):
#         if (not os.path.exists(native_lib_file_name)):
#             raise FileNotFoundError("Could not find specified file {0} to load for {1}".format(native_lib_file_name, readable_lib_name))
#         return native_lib_file_name
#     if (native_lib_file_name is None or native_lib_file_name == ''):
#         raise FileNotFoundError("Invalid empty file name to load for {0}".format(readable_lib_name))
#     native_lib_file_name = _find_first_full_path(native_lib_file_name, env_var_name)
#     return native_lib_file_name

# def _find_first_full_path(short_file_name, env_var_name = ""):
#     if (none_or_empty(short_file_name)):
#         raise Exception("short_file_name")
#     lib_search_path_env_var = env_var_name
#     if (none_or_empty(lib_search_path_env_var)):
#         if(sys.platform == 'win32'):
#             lib_search_path_env_var = "PATH"
#         else:
#             lib_search_path_env_var =  "LD_LIBRARY_PATH"
#     candidates = find_full_path_env_var(short_file_name, lib_search_path_env_var)
#     if ((len(candidates) == 0) and (sys.platform == 'win32')):
#         if (os.path.exists(short_file_name)):
#             candidates = [short_file_name]
#     if (len(candidates) == 0):
#         raise FileNotFoundError("Could not find native library named '{0}' within the directories specified in the '{1}' environment variable".format(short_file_name, lib_search_path_env_var))
#     else:
#         return candidates[0]

# def find_full_path_env_var(dll_short_name, env_var_name="PATH"):
#     x = os.environ.get(env_var_name)
#     if x is not None:
#         search_paths = x.split(os.pathsep)
#     else:
#         search_pathsPathUpdater = [""]
#     return find_full_paths(dll_short_name, search_paths)

# def find_full_paths(dll_short_name, directories = []):
#     full_paths = [os.path.join(d, dll_short_name) for d in directories]
#     return [x for x in full_paths if os.path.exists(x)]

# def none_or_empty(x):
#     return (x is None or x == '')


# # The following is useful, but idiosyncratic. Consider and rethink.
def build_new_path_env (from_env:str='LIBRARY_PATH', to_env:str='PATH', lib_short_fname:str='unknown.dll') -> str:
    """Propose an update to an existing environment variable, based on the path(s) specified in another environment variable. This function is effectively meant to be useful on Windows only.

    Args:
        from_env (str, optional): name of the source environment variable specifying the location(s) of custom libraries to load. Defaults to 'LIBRARY_PATH'.
        to_env (str, optional): environment variable to update, most likely the Windows PATH env var. Defaults to 'PATH'.
        lib_short_fname (str, optional): short file name of the custom library to load. This information is optional and used only for possible warning/log output messages. Defaults to 'unknown.dll'.

    Returns:
        str: the proposed updated content for the 'to_env' environment variable. 
    """    
    if(sys.platform == 'win32'):
        path_sep = ';'
        shared_lib_paths = os.environ.get(from_env)
        if(shared_lib_paths is not None):
            # startup_msg = appendstartup_msg(paste0('Found env var ', from_env, '=', shared_lib_paths), startup_msg)
            arch = os.environ["PROCESSOR_ARCHITECTURE"]
            if arch == 'AMD64':
                subfolder = '64'
            else:
                subfolder = '32'
            shared_lib_paths_vec = shared_lib_paths.split(path_sep)
            return prepend_path_env(shared_lib_paths_vec, subfolder, to_env=to_env)
        else:
            print("WARNING: a function was called to look for environment variable '{0}' to update the environment variable '{1}', but was not found. This may be fine, but if the package fails to load because '{2}' is not found, this is a likely cause.".format(from_env, to_env, lib_short_fname))
            return ""
    else:
        return ""

def update_path_windows (from_env:str='LIBRARY_PATH', to_env:str='PATH', lib_short_fname:str='unknown.dll') -> None:
    """If called on Windows, append an environment variable, based on the path(s) specified in another environment variable. This function is effectively meant to be useful on Windows only.

    Args:
        from_env (str, optional): name of the source environment variable specifying the location(s) of custom libraries to load. Defaults to 'LIBRARY_PATH'.
        to_env (str, optional): environment variable to update, most likely the Windows PATH env var. Defaults to 'PATH'.
        lib_short_fname (str, optional): short file name of the custom library to load. This information is optional and used only for possible warning/log output messages. Defaults to 'unknown.dll'.

    Returns:
        None
    """    
    if(sys.platform == 'win32'):
        os.environ[to_env] = build_new_path_env(from_env, to_env, lib_short_fname)





