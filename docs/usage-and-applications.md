# Usage and applications

## Overview

In computer science, [reference counting](https://en.wikipedia.org/wiki/Reference_counting) is a programming technique of storing the number of references, pointers, or handles to a resource, such as an object, a block of memory, disk space, and others.

This `refcount` package is primarily for managing resources in native libraries, written for instance in C++, from Python. While it boils down to "simply" maintaining a set of counters, **it is deceptively complicated to do so properly** and not end up with memory leaks or crashes. This package offers structured options for reliably managing external native resources. Surprisingly I could not locate an existing python package doing just what I needed. Other use cases requiring reference counting, aside from native library resources, may benefit from reusing and extending classes in `refcount`.

While `refcount` may be used in a variety of contexts, it evolved from use cases needing a Python wrapper around native libraries featuring a C API with opaque pointers (void*), using [cffi](https://cffi.readthedocs.io) for interoperability. This document will not list the many other ways this can be done, nor compare to them.

## Interfacing with a C API

`C` is still the "lingua franca' of in-memory interoperability.

Say we have a C++ library with objects and a C API. The example is contrived for the sake of simplicity.

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

A user experience in Python should be something like this:

```python
dog = Dog()
owner = DogOwner(dog)
owner.say_walk()
print(dog.position)
dog = None # the "native dog" is still alive though, as the owner incremented the ref count. Otherwise, we could have a dreaded segmentation fault.
owner = None
```

We want python objects and functions hiding the low level details close to the C API, in particular the end user should avoiding managing native memory via `release` C API calls, piggybacking the python reference counting instead.

## A real-world use case

Let's look at a (hopefully) more compelling story. `refcount` is used to surface to Python a library to manage data for ensemble time series forecast simulation, [uchronia](https://github.com/csiro-hydroinformatics/uchronia-time-series). An example of such simulations is the [7-day Ensemble Streamflow Forecasts](http://www.bom.gov.au/water/7daystreamflow/) of the Australian Bureau of Meteorology.

The header file for the C API of `uchronia` is in a file [extern_c_api.h](https://github.com/csiro-hydroinformatics/uchronia-time-series/blob/testing/datatypes/include/datatypes/extern_c_api.h)

This C API has function definitions such as:

```c
DATATYPES_API ENSEMBLE_DATA_SET_PTR LoadEnsembleDataset(const char* libraryIdentifier, const char* dataPath);
```

This uses some standard C types such as `char*`, but also an `ENSEMBLE_DATA_SET_PTR`, a pointer to a complex structure/object. Glossing over some details, this object is an instance of a C++ object `TimeSeriesLibrary`, actually of a C++ template class:

```c++
    template<typename T>
    class TTimeSeriesLibrary
```

BUT `class` or `template` are not understood in `C`; from the outside of the library, this is just an opaque pointer `void*`

```c
void* LoadEnsembleDataset(const char* libraryIdentifier, const char* dataPath);
```

This is understandably all scary to most Python aficionados. We want to craft 'pythonic' user experience via [first class python objects](https://github.com/csiro-hydroinformatics/uchronia-time-series/blob/300900d7d1bdba83922081c4e42cb5e671a3ca0c/bindings/python/uchronia/uchronia/classes.py#L55). An example of how it looks from the outside would be:

```python
class TimeSeriesLibrary:
    ###
    def get_series_identifiers(self) -> List['str']:
        ## something magic calling the C API
    def get_series(self, series_identifier:str) -> pd.Series:
        ## something magic calling the C API
```

### How it is done

* **resource management**: `refcount` is the cornerstone managing external resources (data in native memory), saving you from memory leaks or segmentation fault program crashes.
* **data marshalling**: The package [`cinterop`](https://github.com/csiro-hydroinformatics/rcpp-interop-commons/tree/testing/bindings/python/cinterop) offers facilities to convert data in C types (such as `double**`) into, for instance, an [xarray DataArray](https://github.com/pydata/xarray) or [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html) representation.
* **code generation**: Writing and maintening low-level interperability is tedious and bug prone. You'll want to automate and generate everything you can. One such generated code is [uchronia_wrap_generated.py](https://github.com/csiro-hydroinformatics/uchronia-time-series/blob/testing/bindings/python/uchronia/uchronia/wrap/uchronia_wrap_generated.py). Believe it or not, this is not a particularly large API, and code generation is already a must. This is achieved in this case with [c-api-wrapper-generation](https://github.com/csiro-hydroinformatics/c-api-wrapper-generation)
