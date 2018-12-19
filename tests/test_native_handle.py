import os
import sys
from datetime import datetime
import gc

pkg_dir = os.path.join(os.path.dirname(__file__),'..')
sys.path.append(pkg_dir)

from refcount.interop import *
from refcount.putils import library_short_filename


fname = library_short_filename("test_native_library")

if(sys.platform == 'win32'):
    dir_path = os.path.join(pkg_dir, 'tests/test_native_library/x64/Debug')
else:
    dir_path = os.path.join(pkg_dir, 'tests/test_native_library/build')

native_lib_path = os.path.join(dir_path, fname)

assert os.path.exists(native_lib_path)

def test_native_obj_ref_counting():
    dog = Dog()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.add_ref()
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
    #assert 0, owner.native_reference_count)
    #assert 0, dog.native_reference_count)
    assert dog.is_invalid
    assert owner.is_invalid

def test_cffi_native_handle_finalizers():
    initDogCount = Dog.num_native_instances()
    dog = Dog()
    assert (initDogCount + 1) == Dog.num_native_instances()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    # if dog reference a new instance and we force garbage GC:
    gc.collect()
    dog = Dog()
    # var gen = System.GC.GetGeneration(dog)
    gc.collect()
    # gen = System.GC.GetGeneration(dog)
    gc.collect()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    nn = Dog.num_native_instances()
    assert (initDogCount + 1) == nn
    dog = None
    gc.collect()
    assert initDogCount == Dog.num_native_instances()

def test_cffi_native_handle_dispose():
    initDogCount = Dog.num_native_instances()
    dog = Dog()
    assert (initDogCount + 1) == Dog.num_native_instances()
    assert 1 == dog.reference_count
    assert 1 == dog.native_reference_count
    dog.dispose()
    assert initDogCount == Dog.num_native_instances()


# test_native_obj_ref_counting()
# test_cffi_native_handle_finalizers()
# test_cffi_native_handle_dispose()

ut_ffi = FFI()

ut_ffi.cdef('''
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
''')

ut_ffi.cdef('extern void create_date(date_time_interop* start, int year, int month, int day, int hour, int min, int sec);')
ut_ffi.cdef('extern int test_date(date_time_interop* start, int year, int month, int day, int hour, int min, int sec);')
ut_ffi.cdef('extern  void* create_dog();')
ut_ffi.cdef('extern int get_dog_refcount( void* obj);')
ut_ffi.cdef('extern int remove_dog_reference( void* obj);')
ut_ffi.cdef('extern int add_dog_reference( void* obj);')
ut_ffi.cdef('extern  void* create_owner( void* d);')
ut_ffi.cdef('extern int get_owner_refcount( void* obj);')
ut_ffi.cdef('extern int remove_owner_reference( void* obj);')
ut_ffi.cdef('extern int add_owner_reference( void* obj);')
ut_ffi.cdef('extern int num_dogs();')
ut_ffi.cdef('extern int num_owners();')
ut_ffi.cdef('extern void say_walk( void* owner);')
ut_ffi.cdef('extern void release( void* obj);')

ut_dll = ut_ffi.dlopen(native_lib_path, 1) # Lazy loading


class CustomCffiNativeHandle(CffiNativeHandle):
    def __init__(self, pointer, prior_ref_count = 0):
        super(CustomCffiNativeHandle, self).__init__(pointer, type_id='', prior_ref_count = prior_ref_count)

    def _release_handle(self):
        ut_dll.release(self.get_handle());
        return True

class Dog(CustomCffiNativeHandle):
    def __init__(self, pointer = None):
        if pointer is None:
            pointer = ut_dll.create_dog()
        super(Dog, self).__init__(pointer)

    @property
    def native_reference_count(self):
        return ut_dll.get_dog_refcount(self.get_handle())

    @staticmethod
    def num_native_instances():
        return ut_dll.num_dogs()


class DogOwner(CustomCffiNativeHandle):

    def __init__(self, dog):
        super(DogOwner, self).__init__(None)
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

    def _release_handle(self):
        super(DogOwner, self)._release_handle()
        # super(DogOwner, self)._release_handle()
        self.dog.release()
        return True

def test_wrapper_helper_functions():
    assert isinstance(wrap_cffi_native_handle(dict()), dict)
    pointer = ut_dll.create_dog()
    dog = wrap_cffi_native_handle(pointer, 'dog', ut_dll.release)
    assert isinstance(dog, CffiNativeHandle)
    assert dog.is_invalid == False
    assert 1 == dog.reference_count
    assert is_native_handle (dog, 'dog')
    assert is_native_handle (dog, 'cat') == False
    assert is_native_handle (dict()) == False
    assert is_native_handle (1) == False
    assert is_native_handle (1, 'cat') == False
    assert pointer == unwrap_native_handle (dog, False)
    dog = None

