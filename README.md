# refcount

A Python package for reference counting native resources

[![license](http://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/csiro-hydroinformatics/pyrefcount/blob/master/LICENSE.txt) [![Documentation Status](https://readthedocs.org/projects/pyrefcount/badge/?version=latest)](https://pyrefcount.readthedocs.io/en/latest/?badge=latest) ![status](https://img.shields.io/badge/status-beta-blue.svg) master: [![Build status - master](https://ci.appveyor.com/api/projects/status/vmwq7xarxxj8s564/branch/master?svg=true)](https://ci.appveyor.com/project/csiro-hydroinformatics/pyrefcount/branch/master) testing: [![Build status - devel](https://ci.appveyor.com/api/projects/status/vmwq7xarxxj8s564/branch/devel?svg=true)](https://ci.appveyor.com/project/csiro-hydroinformatics/pyrefcount/branch/devel) 

This package is primarily for managing resources in native libraries, written for instance in C++, from Python. While it boils down to "simply" maintaining a set of counters, it is practically complicated to properly do so and not end up with memory leak or crashes. This package aims to offer structured options for managing external native resources - I could not locate a pypi package doing just what I needed. Other use cases requiring reference counting, aside from native library resources, may benefit from reusing and extending classes in `refcount`.

## License

MIT-derived (see [License.txt](./LICENSE.txt))

## Documentation

[pyrefcount at readthedocs](https://pyrefcount.readthedocs.io)

## Installation

```sh
pip install refcount
```

From source:

```sh
pip install -r requirements.txt
python setup.py install
```


## Example

A canonical illustration of the use of this package, based on one of the unit tests. Say we have a C++ library with objects and a C API:

```C++
#define TEST_DOG_PTR  testnative::dog*
#define TEST_OWNER_PTR  testnative::owner*
#define TEST_COUNTED_PTR  testnative::reference_counter*

testnative::dog* create_dog();
testnative::owner* create_owner(testnative::dog* d);
void say_walk(testnative::owner* owner);
void release(testnative::reference_counter* obj);
// etc.
```

From the outside of the library the API is exported with opaque pointers `void*` (C structs pointers and native C99 types could be handled too).

```C++
void* create_dog();
void* create_owner(void* d);
void say_walk(void* owner);
void release(void* obj);
// etc.
```

Starting with the end in mind, from Python we want an API hiding the low level details close to the C API, in particular avoiding managing native memory via `release` C API calls, piggybacking the python GC instead.

```py
dog = Dog()
owner = DogOwner(dog)
owner.say_walk()
print(dog.position)
dog = None # the "native dog" is still alive though, as the owner incremented the ref count
owner = None
```

This is doable with `refcount` and the `cffi` package. One possible design is:

```py
ut_ffi = cffi.FFI()

ut_ffi.cdef('extern void* create_dog();')
ut_ffi.cdef('extern void* create_owner( void* d);')
ut_ffi.cdef('extern void say_walk( void* owner);')
ut_ffi.cdef('extern void release( void* obj);')
# etc.

ut_dll = ut_ffi.dlopen('c:/path/to/test_native_library.dll', 1) # Lazy loading

class CustomCffiNativeHandle(CffiNativeHandle):
    def __init__(self, pointer, prior_ref_count = 0):
        super(CustomCffiNativeHandle, self).__init__(pointer, type_id='', prior_ref_count = prior_ref_count)

    def _release_handle(self) -> bool:
        ut_dll.release(self.get_handle())
        return True

class Dog(CustomCffiNativeHandle):
    def __init__(self, pointer = None):
        if pointer is None:
            pointer = ut_dll.create_dog()
        super(Dog, self).__init__(pointer)
    # etc.

class DogOwner(CustomCffiNativeHandle):

    def __init__(self, dog):
        super(DogOwner, self).__init__(None)
        self._set_handle(ut_dll.create_owner(dog.get_handle()))
        self.dog = dog
        self.dog.add_ref() # Do note this important reference increment

    def say_walk(self):
        ut_dll.say_walk(self.get_handle())

    def _release_handle(self) -> bool:
        super(DogOwner, self)._release_handle()
        # super(DogOwner, self)._release_handle()
        self.dog.release()
        return True
```

### Related work

#### Ancestry

This python package `refcount` actually spawned from prior work for interoperability between C++, R and .NET. The port to Python was also influenced by work authored by Kevin Plastow and undertaken at the Australian Bureau of Meteorology for C/C++/Python interop using `cffi`.

Readers may also want to look at:

* a nuget package [dynamic-interop-dll](https://github.com/rdotnet/dynamic-interop-dll) for .NET/native interop.
* A set of mostly c++ software [tools for interop with C/C++](https://github.com/csiro-hydroinformatics/rcpp-interop-commons)
* A C# library for [generating interop glue code on top of C API glue code](https://github.com/csiro-hydroinformatics/c-api-wrapper-generation).

#### Other python packages

While this present package was authored in part because no existing prior (Python) work could quite fit the need, there are packages that may better address your particular need:

* [infi.pyutils](https://pypi.org/project/infi.pyutils/) contains a reference counting class.
