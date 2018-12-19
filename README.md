# refcount

**Python package for reference counting native pointers**

<!-- [![build](https://img.shields.io/travis/jmp75/pyrefcount.svg?branch=master)](https://travis-ci.org/jmp75/pyrefcount) -->

[![license](http://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/jmp75/pyrefcount/blob/devel/LICENSE.txt)
![status](https://img.shields.io/badge/status-alpha-blue.svg)

<!-- Not sure I will go for coveralls: had issues with pyela:
[![coverage](https://coveralls.io/repos/github/jmp75/pyrefcount/badge.svg?branch=master)](https://coveralls.io/github/jmp75/pyrefcount?branch=master) -->

<!-- [![Docker Build](https://img.shields.io/docker/build/kinverarity/refcount.svg)](https://hub.docker.com/r/kinverarity/refcount/)
[![Build status](https://ci.appveyor.com/api/projects/status/csr7bg8urkbtbq4n?svg=true)](https://ci.appveyor.com/project/kinverarity1/refcount)
[![Python versions](https://img.shields.io/pypi/pyversions/refcount.svg)](https://www.python.org/downloads/) -->
<!-- [![Version](http://img.shields.io/pypi/v/refcount.svg)](https://pypi.python.org/pypi/refcount/) -->

<!-- .. image:: https://img.shields.io/codacy/ad9af103cba14d33abd5b327727ff644.svg 
    :target: https://www.codacy.com/app/matt/striplog/dashboard
    :alt: Codacy code review -->
This package has facilities primarily for managing from Python resources from native libraries written for instance in C++. While it boils down to simply maintaining a set of counters, it is practically complicated to properly do so and not end up with memory leak or crashes. This package aims to offer structured options for managing external native resources. Other use cases requiring reference counting may benefit from reusing and extending classes in refcount.

## License

MIT-derived (see [License.txt](./LICENSE.txt))

## Related work

* list python packages with reference counters facilities
* dynamic-interop
* c-interop
* generating C API glue code

## Installation

```sh
pip install -r requirements.txt
python setup.py install
```

Hopefully soon:

```sh
pip install refcount
```

## Documentation

<!-- See here for the [complete refcount package documentation](https://refcount.readthedocs.io/en/latest/). -->