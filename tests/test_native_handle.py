"""Tests for the handling of native pointers via wrappers and utilities."""

import gc
import os
import sys
from typing import TYPE_CHECKING, Any, Callable, List, Optional

import pytest
from cffi import FFI

if TYPE_CHECKING:
    from refcount.interop import CffiData

from refcount.interop import (
    CffiNativeHandle,
    CffiWrapperFactory,
    DeletableCffiNativeHandle,
    GenericWrapper,
    OwningCffiNativeHandle,
    cffi_arg_error_external_obj_type,
    is_cffi_native_handle,
    unwrap_cffi_native_handle,
    wrap_as_pointer_handle,
    wrap_cffi_native_handle,
)
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
""",
)

ut_ffi.cdef(
    "extern void create_date(date_time_interop* start, int year, int month, int day, int hour, int min, int sec);",
)
ut_ffi.cdef(
    "extern int test_date(date_time_interop* start, int year, int month, int day, int hour, int min, int sec);",
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

ut_ffi.cdef("extern void register_exception_callback(const void* callback);")
ut_ffi.cdef("extern void trigger_callback();")

ut_dll = ut_ffi.dlopen(native_lib_path, ut_ffi.RTLD_LAZY)  # Lazy loading

_message_from_c: str = "<none>"


@ut_ffi.callback("void(char *)")
def called_back_from_c(some_string: str) -> bytes | str:
    """This function is called when uchronia raises an exception.

    It sets the global variable ``_exception_txt_raised_uchronia``.

    :param cdata exception_string: Exception string.
    """
    global _message_from_c  # noqa: PLW0603
    _message_from_c = ut_ffi.string(some_string)


class CustomCffiNativeHandle(CffiNativeHandle):
    """a custom native resource handle for testing purposes."""

    def __init__(self, pointer: "CffiData", type_id: str = "", prior_ref_count: int = 0):
        """Initialize a reference counter for a resource handle, with an initial reference count."""
        super(CustomCffiNativeHandle, self).__init__(
            pointer,
            type_id=type_id,
            prior_ref_count=prior_ref_count,
        )

    def _release_handle(self) -> bool:
        ut_dll.release(self.get_handle())
        return True


class Dog(CustomCffiNativeHandle):
    """A custom class for testing purposes."""

    def __init__(self, pointer: "CffiData" = None):
        """A custom class for testing purposes."""
        if pointer is None:
            pointer = ut_dll.create_dog()
        super(Dog, self).__init__(pointer, type_id="DOG_PTR")

    @property
    def native_reference_count(self) -> int:
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
    def native_reference_count(self) -> int:
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


class CrocFiveParameters(CffiNativeHandle):
    def __init__(
        self,
        pointer: Any,
        release_native: Callable,
        type_id: str = "",
        prior_ref_count: int = 0,
        some_fifth_parameter: float = 0.0,
    ):
        super(CrocFiveParameters, self).__init__(
            pointer,
            type_id=type_id,
            prior_ref_count=prior_ref_count,
        )
        self._release_native_handle = release_native
        self.some_fifth_parameter = some_fifth_parameter

    def _release_handle(self) -> bool:
        self._release_native_handle(self.get_handle())
        return True


class CrocFourParameters(CffiNativeHandle):
    def __init__(
        self,
        pointer: Any,
        release_native: Callable,
        type_id: str = "",
        prior_ref_count: int = 0,
    ):
        super(CrocFourParameters, self).__init__(
            pointer,
            type_id=type_id,
            prior_ref_count=prior_ref_count,
        )
        self._release_native_handle = release_native

    def _release_handle(self) -> bool:
        self._release_native_handle(self.get_handle())
        return True


class CrocFourParametersWrongFourthParameter(CffiNativeHandle):
    def __init__(
        self,
        pointer: Any,
        release_native: Callable,
        type_id: str = "",
        unsupported_argument_type: Optional[List] = None,
    ):
        super(CrocFourParametersWrongFourthParameter, self).__init__(
            pointer,
            type_id=type_id,
            prior_ref_count=0,
        )
        self.unsupported_argument_type = unsupported_argument_type
        self._release_native_handle = release_native

    def _release_handle(self) -> bool:
        self._release_native_handle(self.get_handle())
        return True


class CrocThreeParameters(CrocFourParameters):
    def __init__(self, pointer: Any, release_native: Callable, type_id: str = ""):
        super(CrocThreeParameters, self).__init__(
            pointer,
            release_native=release_native,
            type_id=type_id,
            prior_ref_count=0,
        )


class CrocTwoParameters(CrocThreeParameters):
    def __init__(self, pointer: Any, release_native: Callable):
        super(CrocTwoParameters, self).__init__(
            pointer,
            release_native=release_native,
            type_id="CROC_PTR",
        )


class CrocOneParameters(CrocTwoParameters):
    def __init__(self, pointer: Any):
        super(CrocOneParameters, self).__init__(pointer, release_native=ut_dll.release)


class CrocZeroParameters(CrocOneParameters):
    def __init__(self):
        raise ValueError(
            "This class should not have been used to create a wrapper, since it has no constuctor argument.",
        )
        super(CrocZeroParameters, self).__init__(None)


def test_native_obj_ref_counting():
    dog = Dog()
    assert dog.reference_count == 1
    assert dog.native_reference_count == 1
    dog.add_ref()
    assert dog.reference_count == 2
    assert dog.native_reference_count == 1
    dog.add_ref()
    assert dog.reference_count == 3
    assert dog.native_reference_count == 1
    dog.decrement_ref()
    assert dog.reference_count == 2
    assert dog.native_reference_count == 1
    owner = DogOwner(dog)
    assert owner.reference_count == 1
    assert dog.reference_count == 3
    assert dog.native_reference_count == 1
    dog.release()
    assert owner.reference_count == 1
    assert dog.reference_count == 2
    assert dog.native_reference_count == 1
    dog.release()
    assert owner.reference_count == 1
    assert owner.native_reference_count == 1
    assert dog.reference_count == 1
    assert dog.native_reference_count == 1
    assert not dog.is_invalid
    owner.say_walk()
    owner.release()
    assert owner.reference_count == 0
    assert dog.reference_count == 0
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
    assert dog.reference_count == 1
    assert dog.native_reference_count == 1
    # if dog reference a new instance and we force garbage GC:
    gc.collect()
    dog = Dog()
    gc.collect()
    gc.collect()
    assert dog.reference_count == 1
    assert dog.native_reference_count == 1
    nn = Dog.num_native_instances()
    assert (init_dog_count + 1) == nn
    dog = None
    gc.collect()
    assert init_dog_count == Dog.num_native_instances()


def test_cffi_exceptions():
    import datetime

    incorrect_handle = datetime.datetime(2000, 1, 1, 1, 1, 1)
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
    assert str(dog).startswith(
        'CFFI pointer handle to a native pointer of type id "DOG',
    )
    assert repr(dog).startswith(
        'CFFI pointer handle to a native pointer of type id "DOG',
    )


def test_cffi_native_handle_dispose():
    init_dog_count = Dog.num_native_instances()
    dog = Dog()
    assert str(dog).startswith("CFFI pointer handle to a native pointer")
    assert (init_dog_count + 1) == Dog.num_native_instances()
    assert dog.reference_count == 1
    assert dog.native_reference_count == 1
    dog.dispose()
    assert init_dog_count == Dog.num_native_instances()
    assert dog.reference_count == 0
    # assert 0 == dog.native_reference_count
    # it should be all right to call dispose, even if already called and already zero ref counts.
    dog.dispose()


def test_cffi_handle_access():
    x = ut_ffi.new("char[10]", init=b"foobarbaz0")
    o_wrapper = OwningCffiNativeHandle(x)
    assert str(o_wrapper.ptr) == "<cdata 'char[10]' owning 10 bytes>"
    assert isinstance(o_wrapper.obj, bytes)
    assert o_wrapper.obj == b"f"


from datetime import datetime


def test_wrapper_helper_functions():
    assert isinstance(wrap_cffi_native_handle(dict()), dict)
    pointer = ut_dll.create_dog()
    dog = wrap_cffi_native_handle(pointer, "dog", ut_dll.release)
    assert isinstance(dog, CffiNativeHandle)
    assert dog.is_invalid == False
    assert dog.reference_count == 1
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
    x = datetime(2000, 1, 1, 1, 1)
    assert unwrap_cffi_native_handle(x, False) == x
    with pytest.raises(TypeError):
        assert unwrap_cffi_native_handle(x, True) == x

    from refcount.interop import (
        type_error_cffi,  # backward compat; maintain unit test coverage
    )

    for func in [cffi_arg_error_external_obj_type, type_error_cffi]:
        msg = func(1, "")
        assert msg == "Expected a 'CffiNativeHandle' but instead got object of type '<class 'int'>'"
        msg = func(dog, "cat")
        assert (
            msg == "Expected a 'CffiNativeHandle' with underlying type id 'cat' but instead got one with type id 'dog'"
        )
        msg = func(None, "cat")
        assert msg == "Expected a 'CffiNativeHandle' but instead got 'None'"
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

    x = ut_ffi.new("char[10]", init=b"foobarbaz0")
    assert isinstance(wrap_as_pointer_handle(x, False), OwningCffiNativeHandle)
    assert isinstance(wrap_as_pointer_handle(x, True), OwningCffiNativeHandle)
    assert wrap_as_pointer_handle(dog, False) == dog
    assert wrap_as_pointer_handle(dog, True) == dog

    bb = b"foobarbaz0"
    assert isinstance(wrap_as_pointer_handle(bb, False), GenericWrapper)
    assert isinstance(wrap_as_pointer_handle(bb, True), GenericWrapper)

    d = datetime(2000, 1, 1, 1, 1)
    assert wrap_as_pointer_handle(d, False) == d
    with pytest.raises(TypeError):
        assert unwrap_cffi_native_handle(d, True) == d

    with pytest.raises(
        TypeError,
        match="Argument is neither a CffiNativeHandle nor a CFFI external pointer, nor bytes",
    ):
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
    del x
    gc.collect()
    pointer = ut_dll.create_dog()
    # if strict, we refuse to construct a wrapper outside of the known type identifiers
    with pytest.raises(ValueError):
        _ = wf_strict.create_wrapper(pointer, "THE_THING_PTR", ut_dll.release)
    dog = wf_not_strict.create_wrapper(pointer, "DOG_PTR", ut_dll.release)
    assert isinstance(dog, Dog)
    del dog
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
    anonymous_croc = wf_not_strict.create_wrapper(
        pointer_croc,
        "CROC_PTR",
        ut_dll.release,
    )
    assert isinstance(anonymous_croc, DeletableCffiNativeHandle)
    del anonymous_croc
    gc.collect()


def test_cffi_wrapper_factory_various_ctors():
    """Sweep the various supported wrapper constructors for the wrapper factory"""
    _api_type_wrapper = {"DOG_PTR": Dog, "DOG_OWNER_PTR": DogOwner, "CROC_PTR": None}
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
    del croc_one
    gc.collect()

    # two parameters
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocTwoParameters})
    # if we have two parameters, we need to provide the release function
    with pytest.raises(
        ValueError,
        match="Wrapper class 'CrocTwoParameters' has two constructor arguments; the argument 'release_native' cannot be None",
    ):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=None)
    croc_two = wf_strict.create_wrapper(
        pointer_croc,
        "CROC_PTR",
        release_native=ut_dll.release,
    )
    assert isinstance(croc_two, CrocTwoParameters)
    assert croc_two.type_id == "CROC_PTR"
    assert croc_two._release_handle is not None
    # we cannot test the function equality easily SFAIK
    # assert croc_two._release_handle == ut_dll.release
    del croc_two
    gc.collect()

    # three
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocThreeParameters})

    # if we have three parameters, we need to provide the release function
    with pytest.raises(ValueError):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=None)

    croc_three = wf_strict.create_wrapper(
        pointer_croc,
        "CROC_PTR",
        release_native=ut_dll.release,
    )
    assert isinstance(croc_three, CrocThreeParameters)
    assert croc_three.type_id == "CROC_PTR"
    assert croc_three._release_handle is not None
    # we cannot test the function equality easily SFAIK
    # assert croc_three._release_handle == ut_dll.release
    del croc_three
    gc.collect()

    # four
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocFourParameters})
    # This used not to be supported for a few months, but there is a
    # legacy of classes (in the swift app and more) with an initial ref counter with a zero value default
    # with pytest.raises(NotImplementedError):
    #     _ = wf_strict.create_wrapper(
    #         pointer_croc, "CROC_PTR", release_native=ut_dll.release
    #     )
    croc_four = wf_strict.create_wrapper(
        pointer_croc,
        "CROC_PTR",
        release_native=ut_dll.release,
    )
    assert isinstance(croc_four, CrocFourParameters)
    assert croc_four.type_id == "CROC_PTR"
    assert croc_four._release_handle is not None
    # we cannot test the function equality easily SFAIK
    # assert croc_four._release_handle == ut_dll.release
    del croc_four
    gc.collect()

    # four, but not with the expected fourth parameter
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocFourParametersWrongFourthParameter})
    with pytest.raises(TypeError):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=ut_dll.release)
    # manual cleanup for the sake of being pedantic
    ut_dll.release(pointer_croc)
    gc.collect()

    # five, not supported
    pointer_croc = ut_dll.create_croc()
    _api_type_wrapper.update({"CROC_PTR": CrocFiveParameters})
    with pytest.raises(NotImplementedError):
        _ = wf_strict.create_wrapper(pointer_croc, "CROC_PTR", release_native=ut_dll.release)

    # manual cleanup for the sake of being pedantic
    ut_dll.release(pointer_croc)
    gc.collect()


def test_nativehandle_default_check_valid() -> None:
    # mostly added to increase UT coverage
    # locks in the behavior of the default implementation
    import pytest

    from refcount.base import NativeHandle

    rc = NativeHandle()
    pointer = ut_dll.create_dog()
    dog = wrap_cffi_native_handle(pointer, "dog", ut_dll.release)
    with pytest.raises(NotImplementedError):
        rc._is_valid_handle(dog)
    dog = None
    gc.collect()


def test_callback_via_cffi() -> None:
    # https://github.com/csiro-hydroinformatics/uchronia-time-series/issues/1
    global _message_from_c
    ut_dll.register_exception_callback(called_back_from_c)
    ut_dll.trigger_callback()
    assert _message_from_c != b"<none>"


if __name__ == "__main__":
    test_callback_via_cffi()
