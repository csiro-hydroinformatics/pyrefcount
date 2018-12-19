
class ReferenceCounter(object):
    """A base class for reference counters

    Attributes:
        reference_count (int): property getter, reference count
    """
    def __init__(self, prior_ref_count = 0):
        """initialize this with an initial reference count.
        
        Args:
            prior_ref_count (int): the initial reference count. Default 0 if this object is sole responsible for the lifecycle of the resource.
        """
        self._ref_count = prior_ref_count + 1

    @property
    def reference_count(self):
        """Get the current reference count
        """
        return self._ref_count

    def add_ref(self):
        """Manually increment the reference count. Users should rarely need this unless they have dependencies across reference handles. 
        """
        self._ref_count = self._ref_count + 1

    def decrement_ref(self):
        """Manually decrement the reference count. Users should rarely need this unless they have dependencies across reference handles.
        """
        self._ref_count = self._ref_count - 1


class NativeHandle(ReferenceCounter):
    ''' NativeHandle  A base class for wrappers around otherwise "unmanaged" resources e.g. in a native library.

    Attributes:
        _handle (object): The handle (e.g. cffi pointer) to the native resource.
        _finalizing (bool): a flag telling whether this object is in its deletion phase. This has a use in some advanced cases with reverse callback, possibly not relevant in Python.
    '''
    def __init__(self, handle=None, prior_ref_count = 0):
        """initialize a reference counter for a resource handle, with an initial reference count.
        
        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.
        """
        super(NativeHandle, self).__init__(prior_ref_count)
        # TODO checks 
        self._finalizing = False
        self._handle = None
        if handle is None:
            return # defer setting handle to the inheritor.
        self._set_handle(handle, prior_ref_count)

    def _set_handle(self, handle, prior_ref_count=0):
        """ Sets a handle, performing checks on its acceptability by the inheriting class.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
            prior_ref_count (int): the initial reference count. Default 0 if this NativeHandle is sole responsible for the lifecycle of the resource.

        # Exceptions:
        # error message when a handle is a Zero handle .
        #
        """
        if not self._is_valid_handle(handle):
            raise Exception('The lib.handle argument is not a valid handle')
        self._handle = handle
        self._ref_count = prior_ref_count + 1

    def _is_valid_handle(self, handle):
        """ Checks a handle on its acceptability by the inheriting class. Must be overriden.

        Args:
            handle (object): The handle (e.g. cffi pointer) to the native resource.
        """
        # See also https://stackoverflow.com/questions/4714136/how-to-implement-virtual-methods-in-python
        # May want to make this abstract using ABC - we'll see.
        raise NotImplementedError()


