import os
import sys
from glob import glob

from ctypes.util import find_library as ctypes_find_library

'''This module will host features similar to https://github.com/jmp75/dynamic-interop-dll/blob/master/DynamicInterop/PlatformUtility.cs
'''

def library_short_filename(library_name):
    if library_name is None:
        raise Exception("library_name")
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
