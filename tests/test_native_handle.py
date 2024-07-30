import os
import sys
import gc
from typing import Any, Callable
import pytest
from cffi import FFI
from refcount.interop import CffiNativeHandle, CffiWrapperFactory, DeletableCffiNativeHandle, GenericWrapper, OwningCffiNativeHandle, cffi_arg_error_external_obj_type, is_cffi_native_handle, unwrap_cffi_native_handle, wrap_as_pointer_handle, wrap_cffi_native_handle

from refcount.putils import library_short_filename

fname = library_short_filename("test_native_library")

pkg_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, pkg_dir)
if sys.platform == "win32":
    dir_path = os.path.join(pkg_dir, "tests", "test_native_library", "build", "Debug")
    if not os.path.exists(os.path.join(dir_path, fname)):
        # fallback on AppVeyor output location
        dir_path = os.path.join(pkg_dir, "tests", "test_native_library", "x64", "Debug")

else:
    dir_path = os.path.join(pkg_dir, "tests", "test_native_library", "build")

native_lib_path = os.path.join(dir_path, fname)

assert os.path.exists(native_lib_path)


ut_ffi = FFI()

ut_ffi.cdef(
    """
typedef struct _date_time_interop
{
	int year;
	int month;
	int day;
	int hour;
	int minute;
	int second;
} date_time_interop;

typedef struct _interval_interop
{
	date_time_interop start;
	date_time_interop end;
} interval_interop;
"""
)

ut_ffi.cdef(
    "extern void create_date(date_time_interop* start, int year, int month, int day, int hour, int min, int sec);"
)
ut_ffi.cdef(
    "extern int test_date(date_time_interop* start, int year, int month, int day, int hour, int min, int sec);"
)
ut_ffi.cdef("extern void* create_dog();")
ut_ffi.cdef("extern int get_dog_refcount( void* obj);")
ut_ffi.cdef("extern int remove_dog_reference( void* obj);")
ut_ffi.cdef("extern int add_dog_reference( void* obj);")
ut_ffi.cdef("extern void* create_croc();")
ut_ffi.cdef("extern int get_croc_refcount( void* obj);")
ut_ffi.cdef("extern int remove_croc_reference( void* obj);")
ut_ffi.cdef("extern int add_croc_reference( void* obj);")
ut_ffi.cdef("extern void* create_owner( void* d);")
ut_ffi.cdef("extern int get_owner_refcount( void* obj);")
ut_ffi.cdef("extern int remove_owner_reference( void* obj);")
ut_ffi.cdef("extern int add_owner_reference( void* obj);")
ut_ffi.cdef("extern int num_dogs();")
ut_ffi.cdef("extern int num_owners();")
ut_ffi.cdef("extern void say_walk( void* owner);")
ut_ffi.cdef("extern void release( void* obj);")

ut_dll = ut_ffi.dlopen(native_lib_path, 1)  # Lazy loading


class CustomCffiNativeHandle(CffiNativeHandle):
    def __init__(self, pointer, type_id="", prior_ref_count=0):
        super(CustomCffiNativeHandle, self).__init__(
            pointer, type_id=type_id, prior_ref_count=prior_ref_count
        )

    def _release_handle(self) -> bool:
        ut_dll.release(self.get_handle())
        return True

class Dog(CustomCffiNativeHandle):
    def __init__(self, pointer=None):
        if pointer is None:
            pointer = ut_dll.create_dog()
        super(Dog, self).__init__(pointer, type_id="DOG_PTR")

    @property
    def native_reference_count(self):
        return ut_dll.get_dog_refcount(self.get_handle())

    @staticmethod
    def num_native_instances():
        return ut_dll.num_dogs()


class DogOwner(CustomCffiNativeHandle):
    def __init__(self, dog):
        super(DogOwner, self).__init__(None, type_id="DOG_OWNER_PTR")
        self._set_handle(ut_dll.create_owner(dog.get_handle()))
        self.dog = dog
        self.dog.add_ref()

    @property
    def native_reference_count(self):
        return ut_dll.get_owner_refcount(self.get_handle())

    @staticmethod
    def num_native_instances():
        return ut_dll.num_owners()

    def say_walk(self):
        ut_dll.say_walk(self.get_handle())

    def _release_handle(self) -> bool:
        super(DogOwner, self)._release_handle()
        # super(DogOwner, self)._release_handle()
        self.dog.release()
        return True


class CrocFourParameters(CffiNativeHandle):
    def __init__(self, pointer:Any, release_native:Callable, type_id:str="", prior_ref_count:int=0):
        super(CrocFourParameters, self).__init__(
            pointer, type_id=type_id, prior_ref_count=prior_ref_count
        )
        self._release_native_handle = release_native

    def _release_handle(self) -> bool:
        self._release_native_handle(self.get_handle())
        return True

class CrocThreeParameters(CrocFourParameters):
    def __init__(self, pointer:Any, release_native:Callable, type_id:str=""):
        super(CrocThreeParameters, self).__init__(
            pointer, release_native=release_native, type_id=type_id, prior_ref_count=0
        )

class CrocTwoParameters(CrocThreeParameters):
    def __init__(self, pointer:Any, release_native:Callable):
        super(CrocTwoParameters, self).__init__(
            pointer, release_native=release_native, type_id="CROC_PTR"
        )

class CrocOneParameters(CrocTwoParameters):
    def __init__(self, pointer:Any):
        super(CrocOneParameters, self).__init__(
            pointer, release_native=ut_dll.release
        )

class CrocZeroParameters(CrocOneParameters):
    def __init__(self):
        raise ValueError("This class should not have been used to create a wrapper, since it has no constuctor argument.")
        super(CrocZeroParameters, self).__init__(
            None
        )


def test_native_obj_ref_counting():
    dog = Dog()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.add_ref()
    assert 2 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.add_ref()
    assert 3 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.decrement_ref()
    assert 2 == dog.reference_count
    assert 1 == dog.native_reference_count
    owner = DogOwner(dog)
    assert 1 == owner.reference_count
    assert 3 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.release()
    assert 1 == owner.reference_count
    assert 2 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.release()
    assert 1 == owner.reference_count
    assert 1 == owner.native_reference_count
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    assert not dog.is_invalid
    owner.say_walk()
    owner.release()
    assert 0 == owner.reference_count
    assert 0 == dog.reference_count
    # Cannot check on the native ref count - deleted objects.
    # TODO think of a simple way to test these
    # assert 0, owner.native_reference_count)
    # assert 0, dog.native_reference_count)
    assert dog.is_invalid
    assert owner.is_invalid

def test_cffi_native_handle_finalizers():
    init_dog_count = Dog.num_native_instances()
    dog = Dog()
    assert (init_dog_count + 1) == Dog.num_native_instances()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    # if dog reference a new instance and we force garbage GC:
    gc.collect()
    dog = Dog()
    gc.collect()
    gc.collect()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    nn = Dog.num_native_instances()
    assert (init_dog_count + 1) == nn
    dog = None
    gc.collect()
    assert init_dog_count == Dog.num_native_instances()


def test_cffi_exceptions():
    import datetime
    incorrect_handle = datetime.datetime(2000,1,1,1,1,1)
    with pytest.raises(RuntimeError):
        x = DeletableCffiNativeHandle(incorrect_handle, release_native=None)


def test_generic_wrappers():
    x = ut_ffi.new("char[10]")
    o_wrapper = OwningCffiNativeHandle(x)
    assert str(o_wrapper).startswith("CFFI pointer handle to a native pointer")
    assert o_wrapper.reference_count == 1
    gw = GenericWrapper(o_wrapper.ptr)
    assert gw.ptr == o_wrapper.ptr

def test_str_repr():
    dog = Dog()
    assert str(dog).startswith("CFFI pointer handle to a native pointer of type id \"DOG")
    assert repr(dog).startswith("CFFI pointer handle to a native pointer of type id \"DOG")

def test_cffi_native_handle_dispose():
    init_dog_count = Dog.num_native_instances()
    dog = Dog()
    assert str(dog).startswith("CFFI pointer handle to a native pointer")
    assert (init_dog_count + 1) == Dog.num_native_instances()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.dispose()
    assert init_dog_count == Dog.num_native_instances()
    assert 0 == dog.reference_count
    # assert 0 == dog.native_reference_count
    # it should be all right to call dispose, even if already called and already zero ref counts. 
    dog.dispose()

def test_cffi_handle_access():
    x = ut_ffi.new("char[10]", init="foobarbaz0".encode('utf-8'))
    o_wrapper = OwningCffiNativeHandle(x)
    assert str(o_wrapper.ptr) == "<cdata 'char[10]' owning 10 bytes>"
    assert isinstance(o_wrapper.obj, bytes)
    assert o_wrapper.obj == "f".encode('utf-8')

from datetime import datetime

def test_wrapper_helper_functions():
    assert isinstance(wrap_cffi_native_handle(dict()), dict)
    pointer = ut_dll.create_dog()
    dog = wrap_cffi_native_handle(pointer, "dog", ut_dll.release)
    assert isinstance(dog, CffiNativeHandle)
    assert dog.is_invalid == False
    assert 1 == dog.reference_count
    assert is_cffi_native_handle(dog, "dog")
    assert is_cffi_native_handle(dog, "cat") == False
    assert is_cffi_native_handle(dict()) == False
    assert is_cffi_native_handle(1) == False
    assert is_cffi_native_handle(1, "cat") == False
    assert is_cffi_native_handle(None) == False
    assert pointer == unwrap_cffi_native_handle(dog, False)
    assert pointer == unwrap_cffi_native_handle(dog.ptr, False)
    assert unwrap_cffi_native_handle(None, False) is None
    assert pointer == unwrap_cffi_native_handle(dog, True)
    assert pointer == unwrap_cffi_native_handle(dog.ptr, True)
    assert unwrap_cffi_native_handle(None, True) is None
    x = datetime(2000,1,1,1,1)
    assert unwrap_cffi_native_handle(x, False) == x
    with pytest.raises(TypeError):
        assert unwrap_cffi_native_handle(x, True) == x

    from refcount.interop import type_error_cffi # backward compat; maintain unit test coverage
    for func in [cffi_arg_error_external_obj_type, type_error_cffi]:
        msg = func(1, "")
        assert (
            "Expected a 'CffiNativeHandle' but instead got object of type '<class 'int'>'"
            == msg
        )
        msg = func(dog, "cat")
        assert (
            "Expected a 'CffiNativeHandle' with underlying type id 'cat' but instead got one with type id 'dog'"
            == msg
        )
        msg = func(None, "cat")
        assert (
            "Expected a 'CffiNativeHandle' but instead got 'None'"
            == msg
        )
    dog = None
    gc.collect()

def test_wrap_as_pointer_handle():
    pointer = ut_dll.create_dog()
    dog = wrap_cffi_native_handle(pointer, "dog", ut_dll.release)
    
    # Allow passing None via a wrapper, to facilitate uniform code generation with c-api-wrapper-generation
    assert isinstance(wrap_as_pointer_handle(None, False), GenericWrapper)
    assert isinstance(wrap_as_pointer_handle(None, True), GenericWrapper)
    assert wrap_as_pointer_handle(None, True).ptr is None
    assert wrap_as_pointer_handle(None, False).ptr is None

    x = ut_ffi.new("char[10]", init="foobarbaz0".encode('utf-8'))
    assert isinstance(wrap_as_pointer_handle(x, False), OwningCffiNativeHandle)
    assert isinstance(wrap_as_pointer_handle(x, True), OwningCffiNativeHandle)
    assert wrap_as_pointer_handle(dog, False) == dog
    assert wrap_as_pointer_handle(dog, True) == dog

    bb = "foobarbaz0".encode('utf-8')
    assert isinstance(wrap_as_pointer_handle(bb, False), GenericWrapper)
    assert isinstance(wrap_as_pointer_handle(bb, True), GenericWrapper)

    d = datetime(2000,1,1,1,1)
    assert wrap_as_pointer_handle(d, False) == d
    with pytest.raises(TypeError):
        assert unwrap_cffi_native_handle(d, True) == d

    with pytest.raises(TypeError, match="Argument is neither a CffiNativeHandle nor a CFFI external pointer, nor bytes"):
        nothing = wrap_as_pointer_handle(d, True)

    dog = None
    gc.collect()


def test_cffi_wrapper_factory():

    _api_type_wrapper = {
        "DOG_PTR": Dog,
        "DOG_OWNER_PTR": DogOwner,
    }

    wf_not_strict = CffiWrapperFactory(_api_type_wrapper, False)
    wf_strict = CffiWrapperFactory(_api_type_wrapper, True)
    pointer = ut_dll.create_dog()
    with pytest.raises(ValueError):
        _ = wf_not_strict.create_wrapper(pointer, None, ut_dll.release)
    # https://en.wikipedia.org/wiki/The_Thing_(1982_film)
    x = wf_not_strict.create_wrapper(pointer, "THE_THING_PTR", ut_dll.release)
    assert isinstance(x, DeletableCffiNativeHandle)
    assert not isinstance(x, Dog)
    del(x)
    gc.collect()
    pointer = ut_dll.create_dog()
    # if strict, we refuse to construct a wrapper outside of the known type identifiers
    with pytest.raises(ValueError):
        _ = wf_strict.create_wrapper(pointer, "THE_THING_PTR", ut_dll.release)
    dog = wf_not_strict.create_wrapper(pointer, "DOG_PTR", ut_dll.release)
    assert isinstance(dog, Dog)
    del(dog)
    gc.collect()

    # Test the unexpected cases, where we have a pointer but no 
    # identified native type, and a strict requirement to have one.
    pointer_croc = ut_dll.create_croc()
    with pytest.raises(ValueError):
        wf_strict.create_wrapper(pointer_croc, "CROC_PTR", ut_dll.release)
    # To increase UT coverage mostly, we will test the case where we have a pointer but no identified python wrapper type.
    _api_type_wrapper.update({"CROC_PTR": None})
    with pytest.raises(NotImplementedError):
        wf_strict.create_wrapper(pointer_croc, "CROC_PTR", ut_dll.release)
    # Test the case where we have a pointer but no identified python wrapper type, but we are not strict ad use a generic wrapper.
    anonymous_croc = wf_not_strict.create_wrapper(pointer_croc, "CROC_PTR", ut_dll.release)
    assert isinstance(anonymous_croc, DeletableCffiNativeHandle)
    del(anonymous_croc)
    gc.collect()

def test_cffi_wrapper_factory_various_ctors():
    """Sweep the various supported wrapper constructors for the wrapper factory"""

    _api_type_wrapper = {
        "DOG_PTR": Dog,
        "DOG_OWNER_PTR": DogOwner,
        "CROC_PTR": None
    }
    wf_strict = CffiWrapperFactory(_api_type_wrapper, True)
    # we cannot create a wrapper for a type that has no constructor: how would it know the native pointer?
    _api_type_wrapper.update({"CROC_PTR": CrocZeroParameters})
    pointer_croc = ut_dll.create_croc()
    with pytest.raises(TypeError):
        wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=None)
    # we can create a wrapper with a constructor that has one argument, the pointer
    _api_type_wrapper.update({"CROC_PTR": CrocOneParameters})
    croc_one = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=None)
    assert isinstance(croc_one, CrocOneParameters)
    assert croc_one.type_id == "CROC_PTR"
    assert croc_one._release_handle is not None
    del(croc_one)
    gc.collect()

    # two parameters
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocTwoParameters})
    # if we have two parameters, we need to provide the release function
    with pytest.raises(ValueError, match="Wrapper class 'CrocTwoParameters' has two constructor arguments; the argument 'release_native' cannot be None"):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=None)
    croc_two = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=ut_dll.release)
    assert isinstance(croc_two, CrocTwoParameters)
    assert croc_two.type_id == "CROC_PTR"
    assert croc_two._release_handle is not None
    # we cannot test the function equality easily SFAIK
    # assert croc_two._release_handle == ut_dll.release
    del(croc_two)
    gc.collect()

    # three
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocThreeParameters})

    # if we have three parameters, we need to provide the release function
    with pytest.raises(ValueError):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=None)

    croc_three = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=ut_dll.release)
    assert isinstance(croc_three, CrocThreeParameters)
    assert croc_three.type_id == "CROC_PTR"
    assert croc_three._release_handle is not None
    # we cannot test the function equality easily SFAIK
    # assert croc_three._release_handle == ut_dll.release
    del(croc_three)
    gc.collect()

    # four
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocFourParameters})
    # should be not supported yet, though may be in the future with an inial reference count perhaps making sense
    # put in place this test though and let it break if we ever do support it.
    with pytest.raises(NotImplementedError):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=ut_dll.release)
    # manual cleanup for the sake of being pedantic
    ut_dll.release(pointer_croc)
    gc.collect()

def test_nativehandle_default_check_valid() -> None:
    # mostly added to increase UT coverage
    # locks in the behavior of the default implementation
    from refcount.base import NativeHandle
    import pytest
    rc = NativeHandle()
    pointer = ut_dll.create_dog()
    dog = wrap_cffi_native_handle(pointer, "dog", ut_dll.release)
    with pytest.raises(NotImplementedError):
        rc._is_valid_handle(dog)
    dog = None
    gc.collect()

if __name__ == "__main__":
    test_cffi_wrapper_factory()
    pass