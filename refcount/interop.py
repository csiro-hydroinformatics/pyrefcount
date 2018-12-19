
from cffi import FFI
from refcount.base import NativeHandle


class CffiNativeHandle(NativeHandle):
    """ Reference counting wrapper class for CFFI pointers

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _type_id (str or None): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
        _finalizing (bool): a flag telling whether this object is in its deletion phase. This has a use in some advanced cases with reverse callback, possibly not relevant in Python.
    """

    # Say you have a C API as follows:
    # * `void* create_some_object();`
    # * `dispose_of_some_object(void* obj);`
    # and accessing it using Python and CFFI. Users would use the `calllib` function:
    # aLibPointer = callib('mylib', 'create_some_object');
    # but at some point when done need to dispose of it:
    # callib('mylib', 'dispose_of_some_object', aLibPointer);
    # In practice in real systems one quickly ends up with cases 
    # where it is unclear when to dispose of the object. 
    # If you call the `dispose_of_some_object` function more 
    # than once of too soon, you could easily crash the program.
    # CffiNativeHandle is designed to alleviate this headache by 
    # using Matlab native reference counting of `handle` classes to reliably dispose of objects. 

    # This class is originally inspired from a class with a similar purpose in C#. See https://github.com/jmp75/dynamic-interop-dll

    # """ a global function that can be called to release an external pointer """
    # release_callback = None

    def __init__(self, handle, type_id=None, prior_ref_count = 0):
        """initialize a reference counter for a resource handle, with an initial reference count.
        
        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            type_id (str or None): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(CffiNativeHandle, self).__init__(handle, prior_ref_count)
        # TODO checks on handle
        self._type_id = type_id
        self._finalizing = False
        self._handle = None
        # if release_callback is None:
        #     self._release_callback = CffiNativeHandle.release_callback
        # else:
        #     self._release_callback = release_callback
        if handle is None:
            return # defer setting handle to the inheritor.
        self._set_handle(handle, prior_ref_count)

    def _is_valid_handle(self, h):
        """ Checks if the handle is a CFFI CData pointer.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
        """
        return isinstance(h, FFI.CData)

    def __dispose_impl(self, decrement):
        """ An implementation of the dispose method in a 'Dispose' sw pattern. Avoids cyclic method calls.

        Args:
            decrement (bool): indicating whether the reference count should be decreased (possible future uses)
        """
        if self.disposed:
            return
        if decrement:
            self._ref_count = self._ref_count - 1
        if self._ref_count <= 0:
            if self._release_handle():
                self._handle = None
                # if (!_finalizing)
                # GC.SuppressFinalize(this)
         
    @property
    def disposed(self):
        """ bool: has the native object and memory already been disposed of.        
        """
        return self._handle is None

    @property
    def is_invalid(self):
        """ bool: is the underlying handle valid? In practice synonym with the disposed attribute.
        """
        return self._handle is None

    def _release_handle(self):
        """ Must of overriden. Method disposing of the object pointed to by the CFFI pointer (handle)
        """
        # See also https://stackoverflow.com/questions/4714136/how-to-implement-virtual-methods-in-python
        # May want to make this abstract using ABC - we'll see.
        raise NotImplementedError()

    # @property
    # def ptr(self):
    #     """ Return the pointer to a cffi object """
    #     return self._handle


    # @ptr.setter
    # def ptr(self, value):
    #     """ Set the pointer to the cffi object """
    #     self._handle = value

    @property
    def type_id(self):
        """ Return the optional type identifier for the underlying native type """
        return self._type_id

    # @property
    # def obj(self):
    #     """ Return the native object pointed to (cffi object) """
    #     return self._handle

    def __str__(self):
        """ string representation """
        if self.type_id is None or self.type_id == '':
            return 'CFFI pointer handle to a native pointer'
        return 'CFFI pointer handle to a native pointer of type id "' + self.type_id + '"'

    def __repr__(self):
        """ string representation """
        return str(self)

    def __del__(self):
        """ destructor, triggering the release of the underlying handled resource if the reference count is 0 """
        if not self._handle is None:
            # if not self._release_callback is None:
            # Protect against accessing properties
            # of partially constructed objects (May not be an issue in Python?)
            self._finalizing = True
            self.release()

    def dispose(self):
        """ Disposing of the object pointed to by the CFFI pointer (handle) if the reference counts allows it.
        """
        self.__dispose_impl(True)

    def get_handle(self):
        # get_handle = Returns the value of the handle.
        #
        # Returns:
        # The handle (lib.pointer)
        return self._handle

    def release(self):
        """ Manually decrements the reference counter. Triggers disposal if reference count is down to zero.
        """
        self.__dispose_impl(True)


class CallbackDeleteCffiNativeHandle(CffiNativeHandle):
    """ Reference counting wrapper class for CFFI pointers

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _type_id (str or None): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
        _finalizing (bool): a flag telling whether this object is in its deletion phase. This has a use in some advanced cases with reverse callback, possibly not relevant in Python.
    """
    # """ a global function that can be called to release an external pointer """
    # release_callback = None

    def __init__(self, handle, release_callback, type_id=None, prior_ref_count = 0):
        """initialize a reference counter for a resource handle, with an initial reference count.
        
        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            type_id (str or None): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(CallbackDeleteCffiNativeHandle, self).__init__(handle, type_id, prior_ref_count)
        # if release_callback is None:
        #     self._release_callback = CffiNativeHandle.release_callback
        # else:
        self._release_callback = release_callback
        self._set_handle(handle, prior_ref_count)


#' Create a wrapper around an externalptr
#'
#' Create a wrapper around an externalptr
#'
#' @param obj the object to wrap, if this is an externalptr
#' @param type_id a string character that identifies the underlying type of this object.
#' @return an ExternalObjRef if the input is an externalptr, or 'obj' otherwise.
#' @export
def wrap_cffi_native_handle (obj, type_id='', release_callback = None):
    if isinstance(obj, FFI.CData):
        return CallbackDeleteCffiNativeHandle(obj, release_callback=release_callback, type_id=type_id) 
    else:
        return obj


#' Gets an externalptr wrapped in an ExternalObjRef
#'
#' Gets an externalptr wrapped in an ExternalObjRef
#'
#' @param objRef the presumed ExternalObjRef to unwrap
#' @param stringent if TRUE, an error is raised if objRef is neither an  ExternalObjRef nor an externalptr.
#' @return an externalptr, or the input objRef unchanged if objRef is neither an  ExternalObjRef nor an externalptr and not in stringent mode
#' @import methods
#' @export
def unwrap_native_handle (obj_wrapper, stringent=False):
    # 2016-01-28 allowing null pointers, to unlock behavior of EstimateERRISParameters. 
    # Reassess approach, even if other C API function will still catch the issue of null ptrs.
    if obj_wrapper is None:
        return None  
    if isinstance(obj_wrapper, CffiNativeHandle):
        return obj_wrapper.get_handle()
    if isinstance(obj_wrapper, FFI.CData):
        return obj_wrapper
    else:
        if stringent:
            raise Exception('argument is neither a CffiNativeHandle nor a CFFI external pointer')
        else:
            return obj_wrapper


#' Update the PATH env var on windows, to locate an appropriate DLL dependency.
#' 
#' Update the PATH env var on windows. This is a function meant to be used by packages' '.onLoad' functions. 
#' Looks in another env var, then depending on whether the current process is 32 or 64 bits build a path and looks for a specified DLL. 
#' 
#' @param envVarName the environment variable to look for a root for architecture dependent libraries. 
#' @param libfilename name of the DLL sought and that should be present in the architecture (32/64) subfolder.
#' @import stringr
#' @return a character vector, the startup message string resulting from the update process.
#' @export
# updatePathWindows (envVarName='LIBRARY_PATH', libfilename='mylib.dll'):
#   startupMsg <- ''
#   if(Sys.info()['sysname'] == 'Windows') 
  
#     pathSep <- ';'
#     sharedLibPaths <- Sys.getenv(envVarName)
#     if(sharedLibPaths!=''):
#       startupMsg <- appendStartupMsg(paste0('Found env var ', envVarName, '=', sharedLibPaths), startupMsg)
#       rarch <- Sys.getenv('R_ARCH')
#       subfolder <- ifelse(rarch=='/x64', '64', '32')
#       sharedLibPathsVec <- stringr::str_split(sharedLibPaths, pathSep)
#       if(is.list(sharedLibPathsVec)) sharedLibPathsVec <- sharedLibPathsVec[[1]]
#       priorPathEnv <- Sys.getenv('PATH')
#       priorPaths <- stringr::str_split(priorPathEnv,pathSep)
#       if(is.list(priorPaths)) priorPaths <- priorPaths[[1]]
#       stopifnot(is.character(priorPaths))
#       priorPaths <- tolower(priorPaths)
#       newPaths <- priorPaths
#       for(sharedLibPath in sharedLibPathsVec):
#         if(file.exists(sharedLibPath)):
#           fullpath <- base::normalizePath(file.path(sharedLibPath, subfolder))
#           if(file.exists(fullpath)):
#             if(!(tolower(fullpath) %in% priorPaths)):
#               startupMsg <- appendStartupMsg(paste('Appending to the PATH env var:', fullpath), startupMsg)
#               newPaths <- c(newPaths, fullpath)
#              else 
#               startupMsg <- appendStartupMsg(paste('Path', fullpath, 'already found in PATH environment variable'), startupMsg)
            
          
        
      
#       Sys.setenv(PATH=paste(newPaths, sep=pathSep, collapse=pathSep))
    
#     libfullname <- base::normalizePath(Sys.which(libfilename))
#     if(libfullname=='')
#       startupMsg <- appendStartupMsg(paste0('WARNING: Sys.which("',libfilename,'") did not return a file path'), startupMsg)
#      else 
#       startupMsg <- appendStartupMsg(paste0('first ',libfilename,' shared library in PATH: ', libfullname), startupMsg)
    
  
#   return(startupMsg)


#' Is an object a refcount wrapper
#'
#' Is an object a refcount wrapper, and if so of a specified type_id
#'
#' @param x The object to check: is it an ExternalObjRef
#' @param type_id optional, the exact type of the ExternalObjRef to expect
#' @return a logical value
#' @export
def is_native_handle (x, type_id=''):
    if not isinstance(x, CffiNativeHandle):
        return False
    if type_id is None or type_id == '':
        return True
    return (x.type_id == type_id)


#' Build an error message that an unexpected object is in lieu of an expected refcount external ref object.
#'
#' Build an error message that an unexpected object is in lieu of an expected refcount external ref object.
#'
#' @param x actual object that is not of the expected type or underlying type for the external pointer.
#' @param expectedType expected underlying type for the ExternalObj
#' @return a character, the error message
#' @export
# argErrorExternalObjType (x, expectedType):
#   if(!isExternalObjRef(x)):
#     return(paste0('Expected type "', expectedType, '" but got object of type "', typeof(x), '" and class "', class(x), '"' ))
#    else 
#     return(paste0('Expected ExternalObj type "', expectedType, '" but got ExternalObj type "', x@type))
  