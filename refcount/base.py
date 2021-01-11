
from typing import Any


class ReferenceCounter(object):
    """A base class for reference counters

    Attributes:
        reference_count (int): property getter, reference count
    """
    def __init__(self, prior_ref_count:int = 0):
        """initialize this with an initial reference count.
        
        Args:
            prior_ref_count (int): the initial reference count. Default 0 if this object is sole responsible for the lifecycle of the resource.
        """
        self._ref_count:int = prior_ref_count + 1

    @property
    def reference_count(self) -> int:
        """Get the current reference count
        """
        return self._ref_count

    def add_ref(self):
        """Manually increment the reference count. 
        
        Users usually have no need to call this method. They may have to if they 
        manage cases where one native handle wrapper uses another wrapper (and its underlying resource). 
        """
        self._ref_count = self._ref_count + 1

    def decrement_ref(self):
        """Manually increment the reference count. 
        
        Users usually have no need to call this method. They may have to if they 
        manage cases where one native handle wrapper uses another wrapper (and its underlying resource). 
        """
        self._ref_count = self._ref_count - 1

class NativeHandle(ReferenceCounter):
    '''A base class for wrappers around otherwise "unmanaged" resources e.g. in a native library.

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _finalizing (bool): a flag telling whether this object is in its deletion phase. This has a use in some advanced cases with reverse callback, possibly not relevant in Python.
    '''
    def __init__(self, handle:Any=None, prior_ref_count:int = 0):
        """initialize a reference counter for a resource handle, with an initial reference count.
        
        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(NativeHandle, self).__init__(prior_ref_count)
        # TODO checks 
        self._finalizing:bool = False
        self._handle:Any = None
        if handle is None:
            return # defer setting handle to the inheritor.
        self._set_handle(handle, prior_ref_count)

    def _set_handle(self, handle:Any, prior_ref_count:int=0):
        """ Sets a handle, after performing checks on its suitability as a handle for this object.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.

        Exceptions:
            error message when a handle is not a valid object.
        """
        if not self._is_valid_handle(handle):
            raise Exception('The handle argument is not a valid handle')
        self._handle = handle
        self._ref_count = prior_ref_count + 1

    def _is_valid_handle(self, handle:Any) -> bool:
        """ Checks a handle on its suitability as a handle for this object. 
        This method must be overriden by the inheritors.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
        """
        # See also https://stackoverflow.com/questions/4714136/how-to-implement-virtual-methods-in-python
        # May want to make this abstract using ABC - we'll see.
        raise NotImplementedError()


