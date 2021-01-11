
from typing import Any, Callable, Union
from cffi import FFI
from refcount.base import NativeHandle

# This is a Hack. I cannot use FFI.CData in type hints.
CffiData = Any

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

    # This class is originally inspired from a class with a similar purpose in C#. See https://github.com/rdotnet/dynamic-interop-dll

    # """ a global function that can be called to release an external pointer """
    # release_callback = None

    def __init__(self, handle, type_id:str=None, prior_ref_count:int = 0):
        """Initialize a reference counter for a resource handle, with an initial reference count.
        
        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            type_id (str or None): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(CffiNativeHandle, self).__init__(handle, prior_ref_count)
        # TODO checks on handle
        self._type_id:str = type_id
        self._finalizing:bool = False
        self._handle:CffiData = None
        # if release_callback is None:
        #     self._release_callback = CffiNativeHandle.release_callback
        # else:
        #     self._release_callback = release_callback
        if handle is None:
            return # defer setting handle to the inheritor.
        self._set_handle(handle, prior_ref_count)

    def _is_valid_handle(self, h:CffiData) -> bool:
        """ Checks if the handle is a CFFI CData pointer, acceptable handle for this wrapper.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
        """
        return isinstance(h, FFI.CData)

    def __dispose_impl(self, decrement:bool):
        """ An implementation of the dispose method in a 'Dispose' software pattern. Avoids cyclic method calls.

        Args:
            decrement (bool): indicating whether the reference count should be decreased. It should almost always be True except in very unusual use cases (argument is for possible future use).
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
        """Has the native object and memory already been disposed of.

        Returns:
            (bool): The underlying native handle has been disposed of from this wrapper
        """
        return self._handle is None

    @property
    def is_invalid(self):
        """Is the underlying handle valid? In practice synonym with the disposed attribute.

        Returns:
            (bool): True if this handle is valid 
        """
        return self._handle is None

    def _release_handle(self) -> bool:
        """ Must of overriden. Method disposing of the object pointed to by the CFFI pointer (handle)

        Raises:
            NotImplementedError: thrown if this method is not overriden by inheritors

        Returns:
            bool: Overriding implementation should return True if the release of native resources was successful, False otherwise.
        """
        # See also https://stackoverflow.com/questions/4714136/how-to-implement-virtual-methods-in-python
        # May want to make this abstract using ABC - we'll see.
        raise NotImplementedError()
        return False

    def get_handle(self) -> Union[CffiData, None]:
        """Gets the underlying low-level CFFI handle this object wraps

        Returns:
            (Union[CffiData, None]): CFFI handle or None
        """
        return self._handle

    # TODO?
    # @property.getter
    # def ptr(self):
    #     """ Return the pointer to a cffi object """
    #     return self._handle

    @property
    def type_id(self) ->str:
        """ Return an optional type identifier for the underlying native type.

        This can be in practice useful to be more transparent about the underlying 
        type obtained via a C API with opaque pointers (i.e. void*)

        Returns:
            str: optional type identifier
        """
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
        _release_callback (callable): function to call on deleting this wrapper. The function should have one argument accepting the object _handle.
    """
    # """ a global function that can be called to release an external pointer """
    # release_callback = None

    def __init__(self, handle:CffiData, release_callback:Callable[[CffiData],None], type_id:str=None, prior_ref_count:int = 0):
        """New reference counter for a CFFI resource handle.

        Args:
            handle (CffiData): The handle (expected cffi pointer) to the native resource.
            release_callback (Callable[[CffiData],None]): function to call on deleting this wrapper. The function should have one argument accepting the object handle.
            type_id (str, optional): [description]. An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation. Defaults to None.
            prior_ref_count (int, optional): [description]. The initial reference count. Defaults to 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(CallbackDeleteCffiNativeHandle, self).__init__(handle, type_id, prior_ref_count)
        self._release_callback:Callable[[CffiData],None] = release_callback
        self._set_handle(handle, prior_ref_count)

    def _release_handle(self) -> bool:
        """ Manually decrements the reference counter. Triggers disposal if reference count is reaching down to zero.

        Returns:
            bool: Overriding implementation should return True if the release of native resources handle was successful, False otherwise.
        """
        if self._handle is None:
            return False
        if self._release_callback is None:
            return False
        if self._release_callback is not None:
            self._release_callback(self._handle) # TODO are trapped exceptions acceptable here? 
            return True

def wrap_cffi_native_handle(obj:Union[CffiData,Any], type_id:str='', release_callback:Callable[[CffiData],None] = None) -> Union[CallbackDeleteCffiNativeHandle,Any]:
    """ Create a reference counting wrapper around an object if this object is a CFFI pointer

    Args:
        obj (Union[CffiData,Any]): An object, which will be wrapped if this is a CFFI pointer, i.e. an instance of `CffiData`
        release_callback (Callable[[CffiData],None]): function to call on deleting this wrapper. The function should have one argument accepting the object handle.
        type_id (str or None): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
    """
    if isinstance(obj, FFI.CData):
        return CallbackDeleteCffiNativeHandle(obj, release_callback=release_callback, type_id=type_id) 
    else:
        return obj

def is_cffi_native_handle(x:Any, type_id:str='') -> bool:
    """ Checks whether an object is a ref counting wrapper around a CFFI pointer

    Args:
        x (object): object to test, presumed to be an instance of `CffiNativeHandle`
        type_id (str or None): Optional identifier for the type of underlying resource being wrapped.
    """
    if x is None:
        return False
    if not isinstance(x, CffiNativeHandle):
        return False
    if type_id is None or type_id == '':
        return True
    return (x.type_id == type_id)

def unwrap_cffi_native_handle(obj_wrapper:Any, stringent:bool=False) -> Union[CffiData,Any,None]:
    """ Unwrap a reference counting wrapper and returns its CFFI pointer if it is found (wrapped or 'raw')

    Args:
        obj_wrapper (Any): An object, which will be unwrapped if this is a CFFI pointer, i.e. an instance of `CffiData`
        stringent (bool, optional): [description]. if True an error is raised if obj_wrapper is neither None, a CffiNativeHandle nor an CffiData. Defaults to False.

    Raises:
        Exception: A CFFI pointer could not be found in the object.

    Returns:
        Union[CffiData,Any,None]: A CFFI pointer if it was found. Returns None or unchanged if not found, and stringent is equal to False. Exception otherwise.
    """    
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
            raise Exception('Argument is neither a CffiNativeHandle nor a CFFI external pointer')
        else:
            return obj_wrapper

def cffi_arg_error_external_obj_type(x:Any, expected_type_id:str):
    """Build an error message that an unexpected object is in lieu of an expected refcount external ref object.

    Args:
        x (object): object passed as an argument to a function but with an unexpected type or type id.
        expected_type_id (str or None): Expected identifier for the type of underlying resource being wrapped.

    Returns: (str): the error message
    """
    if x is None:
        return "Expected a 'CffiNativeHandle' but instead got 'None'"
    if not is_cffi_native_handle(x):
        return "Expected a 'CffiNativeHandle' but instead got object of type '{0}'".format(str(type(x)))
    else:
        return "Expected a 'CffiNativeHandle' with underlying type id '{0}' but instead got one with type id '{1}'".format(expected_type_id, x.type_id)

# Maybe, pending use cases:
# def checked_unwrap_cffi_native_handle (obj_wrapper, stringent=False):
#     if not is_cffi_native_handle (obj_wrapper, expected_type_id):
#         raise Exception(cffi_arg_error_external_obj_type(obj_wrapper, expected_type_id)
#     else:
#         return unwrap_cffi_native_handle (obj_wrapper, stringent=True)

