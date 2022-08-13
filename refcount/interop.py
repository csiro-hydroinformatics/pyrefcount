"""Implementation of reference counting classes for external resources accessed via interoperability software such as cffi
"""

from typing import Any, Callable, Dict, Optional, Union
from typing_extensions import TypeAlias 

from cffi import FFI
from refcount.base import NativeHandle

# This is a Hack. I cannot use FFI.CData in type hints.
# CffiData: TypeAlias = FFI().CData
CffiData: TypeAlias = Any
"""A dummy type to use in type hints for limited documentation purposes

FFI.CData is a type, but it seems it cannot be used in type hinting.
"""


class CffiNativeHandle(NativeHandle):
    """Reference counting wrapper class for CFFI pointers

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _type_id (Optional[str]): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
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

    def __init__(self, handle: "CffiData", type_id: str = None, prior_ref_count: int = 0):
        """Initialize a reference counter for a resource handle, with an initial reference count.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            type_id (Optional[str]): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(CffiNativeHandle, self).__init__(handle, prior_ref_count)
        # TODO checks on handle
        self._type_id = type_id
        self._finalizing: bool = False
        self._handle: "CffiData" = None
        if handle is None:
            return  # defer setting the handle to the inheritor.
        self._set_handle(handle, prior_ref_count)

    def _is_valid_handle(self, h: "CffiData") -> bool:
        """Checks if the handle is a CFFI CData pointer, acceptable handle for this wrapper.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
        """
        return isinstance(h, FFI.CData)

    def __dispose_impl(self, decrement: bool) -> None:
        """An implementation of the dispose method in a 'Dispose' software pattern. Avoids cyclic method calls.

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

    @property
    def disposed(self) -> bool:
        """Has the native object and memory already been disposed of.

        Returns:
            (bool): The underlying native handle has been disposed of from this wrapper
        """
        return self._handle is None

    @property
    def is_invalid(self) -> bool:
        """Is the underlying handle valid? In practice synonym with the disposed attribute.

        Returns:
            (bool): True if this handle is valid
        """
        return self._handle is None

    def _release_handle(self) -> bool:
        """Must of overriden. Method disposing of the object pointed to by the CFFI pointer (handle)

        Raises:
            NotImplementedError: thrown if this method is not overriden by inheritors

        Returns:
            bool: Overriding implementation should return True if the release of native resources was successful, False otherwise.
        """
        # See also https://stackoverflow.com/questions/4714136/how-to-implement-virtual-methods-in-python
        # May want to make this abstract using ABC - we'll see.
        raise NotImplementedError("method _release_handle must be overriden by child classes")

    def get_handle(self) -> Union["CffiData", None]:
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
    def type_id(self) -> Optional[str]:
        """Return an optional type identifier for the underlying native type.

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

    def __str__(self) -> str:
        """ string representation """
        if self.type_id is None or self.type_id == "":
            return "CFFI pointer handle to a native pointer " + str(self._handle)
        return 'CFFI pointer handle to a native pointer of type id "' + self.type_id + '"'

    @property
    def ptr(self) -> 'CffiData':
        """ Return the pointer (cffi object) """
        return self._handle

    @property
    def obj(self) -> Any:
        """ Return the object pointed to (cffi object) """
        return self._handle[0]


    def __repr__(self) -> str:
        """ string representation """
        return str(self)

    def __del__(self) -> None:
        """ destructor, triggering the release of the underlying handled resource if the reference count is 0 """
        if self._handle is not None:
            # if not self._release_native is None:
            # Protect against accessing properties
            # of partially constructed objects (May not be an issue in Python?)
            self._finalizing = True
            self.release()

    def dispose(self) -> None:
        """Disposing of the object pointed to by the CFFI pointer (handle) if the reference counts allows it."""
        self.__dispose_impl(True)

    def release(self) -> None:
        """Manually decrements the reference counter. Triggers disposal if reference count is down to zero."""
        self.__dispose_impl(True)


class DeletableCffiNativeHandle(CffiNativeHandle):
    """Reference counting wrapper class for CFFI pointers

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _type_id (Optional[str]): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
        _finalizing (bool): a flag telling whether this object is in its deletion phase. This has a use in some advanced cases with reverse callback, possibly not relevant in Python.
        _release_native (Callable[[CffiData],None]): function to call on deleting this wrapper. The function should have one argument accepting the object _handle.
    """

    def __init__(
        self,
        handle: "CffiData",
        release_native: Optional[Callable[["CffiData"], None]],
        type_id: str = None,
        prior_ref_count: int = 0,
    ):
        """New reference counter for a CFFI resource handle.

        Args:
            handle (CffiData): The handle (expected cffi pointer) to the native resource.
            release_native (Callable[[CffiData],None]): function to call on deleting this wrapper. The function should have one argument accepting the object handle.
            type_id (str, optional): [description]. An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation. Defaults to None.
            prior_ref_count (int, optional): [description]. The initial reference count. Defaults to 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(DeletableCffiNativeHandle, self).__init__(
            handle, type_id, prior_ref_count
        )
        self._release_native = release_native
        self._set_handle(handle, prior_ref_count)

    def _release_handle(self) -> bool:
        """Release the handle, dispose of the native resource.

        Returns:
            bool: Return True if the release of native resources handle was successful, False otherwise.
        """
        if self._handle is None:
            return False
        if self._release_native is None:
            return False
        if self._release_native is not None:
            self._release_native(
                self._handle
            )  # TODO are trapped exceptions acceptable here?
            return True


class OwningCffiNativeHandle(CffiNativeHandle):
    """Reference counting wrapper class for CFFI pointers that own and already manage the native memory

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _type_id (Optional[str]): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
        _finalizing (bool): a flag telling whether this object is in its deletion phase. This has a use in some advanced cases with reverse callback, possibly not relevant in Python.
    """

    # """ a global function that can be called to release an external pointer """
    # release_native = None

    def __init__(
        self,
        handle: "CffiData",
        type_id: str = None,
        prior_ref_count: int = 0,
    ):
        """Reference counting wrapper class for CFFI pointers that own and already manage the native memory

        Args:
            handle (CffiData): The handle (expected cffi pointer) to the native resource.
            type_id (str, optional): [description]. An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation. Defaults to None.
            prior_ref_count (int, optional): [description]. The initial reference count. Defaults to 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(OwningCffiNativeHandle, self).__init__(
            handle, type_id, prior_ref_count
        )
        self._set_handle(handle, prior_ref_count)

    def _release_handle(self) -> bool:
        """Does nothing, as the wrapped cffi pointer is already owning and managing the memory

        Returns:
            bool: Always returns True.
        """
        return True


def wrap_cffi_native_handle(
    obj: Union["CffiData", Any],
    type_id: str = "",
    release_native: Callable[["CffiData"], None] = None,
) -> Union[DeletableCffiNativeHandle, Any]:
    """Create a reference counting wrapper around an object if this object is a CFFI pointer

    Args:
        obj (Union[CffiData,Any]): An object, which will be wrapped if this is a CFFI pointer, i.e. an instance of `CffiData`
        release_native (Callable[[CffiData],None]): function to call on deleting this wrapper. The function should have one argument accepting the object handle.
        type_id (Optional[str]): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
    """
    if isinstance(obj, FFI.CData):
        return DeletableCffiNativeHandle(
            obj, release_native=release_native, type_id=type_id
        )
    else:
        return obj


def is_cffi_native_handle(x: Any, type_id: str = "") -> bool:
    """Checks whether an object is a ref counting wrapper around a CFFI pointer

    Args:
        x (object): object to test, presumed to be an instance of `CffiNativeHandle`
        type_id (Optional[str]): Optional identifier for the type of underlying resource being wrapped.
    """
    if x is None:
        return False
    if not isinstance(x, CffiNativeHandle):
        return False
    if type_id is None or type_id == "":
        return True
    return x.type_id == type_id


def unwrap_cffi_native_handle(
    obj_wrapper: Any, stringent: bool = False
) -> Union["CffiData", Any, None]:
    """Unwrap a reference counting wrapper and returns its CFFI pointer if it is found (wrapped or 'raw')

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
            raise TypeError(
                "Argument is neither a CffiNativeHandle nor a CFFI external pointer"
            )
        else:
            return obj_wrapper


def cffi_arg_error_external_obj_type(x: Any, expected_type_id: str) -> str:
    """Build an error message that an unexpected object is in lieu of an expected refcount external ref object.

    Args:
        x (object): object passed as an argument to a function but with an unexpected type or type id.
        expected_type_id (Optional[str]): Expected identifier for the type of underlying resource being wrapped.

    Returns (str): the error message
    """
    if x is None:
        return "Expected a 'CffiNativeHandle' but instead got 'None'"
    if not is_cffi_native_handle(x):
        return (
            "Expected a 'CffiNativeHandle' but instead got object of type '{0}'".format(
                str(type(x))
            )
        )
    else:
        return "Expected a 'CffiNativeHandle' with underlying type id '{0}' but instead got one with type id '{1}'".format(
            expected_type_id, x.type_id
        )


# Maybe, pending use cases:
# def checked_unwrap_cffi_native_handle (obj_wrapper, stringent=False):
#     if not is_cffi_native_handle (obj_wrapper, expected_type_id):
#         raise Exception(cffi_arg_error_external_obj_type(obj_wrapper, expected_type_id)
#     else:
#         return unwrap_cffi_native_handle (obj_wrapper, stringent=True)

class GenericWrapper:
    """A pass-through wrapper for python objects that are ready for C interop. "bytes" can be passed as C 'char*'

    This is mostly a facility to generate glue code more easily 
    """    

    def __init__(self, handle: Any):
        self._handle = handle

    @property
    def ptr(self) -> Any:
        return self._handle

def wrap_as_pointer_handle(
    obj_wrapper: Any, stringent: bool = False
) -> Union[CffiNativeHandle, OwningCffiNativeHandle, GenericWrapper, None]:
    """Wrap an object, if need be, so that its C API pointer appears accessible via a 'ptr' property

    Args:
        obj_wrapper (Any): Object to wrap, if necessary
        stringent (bool, optional): Throws an exception if the input type is unhandled. Defaults to False.

    Raises:
        TypeError: neither a CffiNativeHandle nor a CFFI external pointer, nor bytes

    Returns:
        Union[CffiNativeHandle, OwningCffiNativeHandle, GenericWrapper, None]: wrapped object or None
    """    
    # 2016-01-28 allowing null pointers, to unlock behavior of EstimateERRISParameters.
    # Reassess approach, even if other C API function will still catch the issue of null ptrs.
    if obj_wrapper is None:
        return None
        # return GenericWrapper(FFI.NULL)  # Ended with kernel crashes and API call return, but unclear why
    elif isinstance(obj_wrapper, CffiNativeHandle):
        return obj_wrapper
    elif isinstance(obj_wrapper, FFI.CData):
        return OwningCffiNativeHandle(obj_wrapper)
    elif isinstance(obj_wrapper, bytes):
        return GenericWrapper(obj_wrapper)
    else:
        if stringent:
            raise TypeError(
                "Argument is neither a CffiNativeHandle nor a CFFI external pointer, nor bytes"
            )
        else:
            return obj_wrapper


def type_error_cffi(x:Union[CffiNativeHandle, Any], expected_type:str) -> str:
    """DEPRECATED Build an error message for situations where a cffi pointer handler is not that, or not of the expected type

    Args:
        x (Union[CffiNativeHandle, Any]): actual object that is not of the expected type or underlying type for the external pointer.
        expected_type (str): underlying type expected for the CFFI pointer handler

    Returns:
        str: error message that the caller can use to report the issue
    """
    return cffi_arg_error_external_obj_type(x, expected_type)

class CffiWrapperFactory:
    """A class that creates custom python wrappers based on the type identifier of the external pointer being wrapped
    """
    def __init__(self, api_type_wrapper:Dict[str,Any], strict_wrapping:bool=False) -> None:
        """_summary_

        Args:
            api_type_wrapper (Dict[str,Any]): dictionary, mapping from type identifiers to callables, class constructors
            strict_wrapping (bool, optional): If true, type identifiers passed at wrapper creation time `create_wrapper` 
                must be known or exceptions are raised. If False, it falls back on creating generic wrappers. Defaults to False.
        """        
        self._strict_wrapping = strict_wrapping
        self._api_type_wrapper = api_type_wrapper

    def create_wrapper(self, obj: Any, type_id: str, release_native: Optional[Callable[["CffiData"], None]]) -> 'CffiNativeHandle':
        """_summary_

        Args:
            obj (Union[CffiData,Any]): An object, which will be wrapped if this is a CFFI pointer, i.e. an instance of `CffiData`
            type_id (Optional[str]): An optional identifier for the type of underlying resource. This can be used to usefully maintain type information about the pointer/handle across an otherwise opaque C API. See package documentation.
            release_native (Callable[[CffiData],None]): function to call on deleting this wrapper. The function should have one argument accepting the object handle.

        Raises:
            ValueError: Missing type_id
            ValueError: If this object is in strict mode, and `type_id` is not known in the mapping
            NotImplementedError: `type_id` is known, but mapping to None (wrapper not yet implemented)
            TypeError: The function to create the wrapper does not accept any argument. 

        Returns:
            CffiNativeHandle: cffi wrapper
        """        
        from inspect import signature
        if type_id is None:
            raise ValueError("Type ID provided cannot be None")
        if type_id not in self._api_type_wrapper.keys():
            if self._strict_wrapping:
                raise ValueError("Type ID {} is unknown".format(type_id))
            else:
                return wrap_cffi_native_handle(obj, type_id, release_native)
        wrapper_type = self._api_type_wrapper[type_id]
        if wrapper_type is None:
            if self._strict_wrapping:
                raise NotImplementedError(
                    "Python object wrapper for foreign type ID {} is not yet implemented".format(
                        wrapper_type
                    )
                )
            else:
                return wrap_cffi_native_handle(obj, type_id, release_native)
        else:
            s = signature(wrapper_type)
            n = len(s.parameters)
            if n == 0:
                raise TypeError("Wrapper constructor must have at least one argument")
            elif n == 1:
                return wrapper_type(obj)
            elif n == 2:
                return wrapper_type(obj, release_native)
            else:
                return wrapper_type(obj, release_native, type_id)


WrapperCreationFunction = Callable[[Any, str, Callable], DeletableCffiNativeHandle]
