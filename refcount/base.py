
class ReferenceCounter(object):
    def __init__(self, prior_ref_count = 0):
        self._ref_count = prior_ref_count + 1

    # reference_count - The number of references to the underlying object.
    # In practice this would almost always be 0 or 1 and users should not need to take use this. 
    @property
    def reference_count(self):
        return self._ref_count

    def add_ref(self):
        # add_ref - Manually increments the reference counter.
        # This is very unusual you would need to call this method. 
        self._ref_count = self._ref_count + 1

    def decrement_ref(self):
        self._ref_count = self._ref_count - 1


class NativeHandle(ReferenceCounter):
    ''' NativeHandle  A base class for wrappers around objects in native libraries for easier memory management. 
    '''

    """ Thin wrapper around a native pointer (cffi object) """
    def __init__(self, handle=None, prior_ref_count = 0):
        super(NativeHandle, self).__init__(prior_ref_count)
        # TODO checks on ptr
        self._finalizing = False
        self._handle = None
        if handle is None:
            return # defer setting handle to the inheritor.
        self._set_handle(handle, prior_ref_count)

    def _set_handle(self, handle, prior_ref_count=0):
        # _set_handle - Sets a handle.
        #
        # Parameters:
        #   handle:
        # The handle (lib.handle), value of the handle to the native object
        #
        #   prior_ref_count:
        # (Optional) Number of pre-existing references for 
        # the native object. Almost always 0 except in unusual, advanced situations.
        #
        # Exceptions:
        # error message when a handle is a Zero handle .
        #
        # Remarks:
        # If a native object was created prior to its use by Matlab, its lifetime may need
        # to extend beyong its use from Matlab, hence the provision for an initial reference 
        # count more than 0. In practice the scenario is very unusual.
        if not self._is_valid_handle(handle):
            raise Error('The lib.handle argument is not a valid handle')
        self._handle = handle
        self._ref_count = prior_ref_count + 1

    def _is_valid_handle(self, handle):
        # See also https://stackoverflow.com/questions/4714136/how-to-implement-virtual-methods-in-python
        # May want to make this abstract using ABC - we'll see.
        raise NotImplementedError()


