# Changelog

<!-- insertion marker -->

## v1.2.0 (2023-01-25)

`wrap_as_pointer_handle` wraps `None` via a `GenericWrapper`, to facilitate code generation on top of a C API allowing `nullptr` to be passed in.

## v1.1.1 (2022-08-19)

Minor changes that may not have been required to build the [conda package](https://github.com/conda-forge/refcount-feedstock/pull/2)

## v1.1.0 (2022-08-19)

### Main changes

* Expand some features to cater for macos
* Tidy up and reengineer some of the legacy functions in the platform utilities `putils` to facilitate library loading. Minor breaking changes, but probably for no-one but the author in effect.

## v1.0.0 (2022-08-13)

### Main changes

* Improve documentation, and use the mkdocs-material theme
* mkdocs.yml changes. Enable dark/light modes from mkdocs-material
* Improved type hints, and add static type checks (mypy)
* Improve unit tests and add unit test code coverage reporting
* Manage the package using poetry; phase out setuptools.
* Apply some of the approaches in https://py-pkgs.org.
* Restore appveyor CI to a working state

## v0.9.3 (2022-01-24)

### Feature

* Add a class CffiWrapperFactory
