# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v1.2.7](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.2.7) - 2025-01-14

<small>[Compare with v1.2.6](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v1.2.6...v1.2.7)</small>

### Build

Functionally unchanged, the package has been migrated away from using `poetry` and some legacy steps for building to the template [copier-uv](https://pawamoy.github.io/copier-uv/).

- update cffi dependency version to the latest. Building older cffi fails on GH actions ([e4e603d](https://github.com/csiro-hydroinformatics/pyrefcount/commit/e4e603da271d6b955eae5baacb9362fe7c519a7e) by J-M).
- cumulative changes until `make check` passes ([ccf1a18](https://github.com/csiro-hydroinformatics/pyrefcount/commit/ccf1a181e096446c595dc315bc2e2c3e35a18fbf) by J-M).

## [v1.2.6](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.2.6) - 2024-11-05

<small>[Compare with v1.2.5](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v1.2.5...v1.2.6)</small>

* Use proper ffi.RTLD_LAZY flag with cffi, in the unit tests. Related issue was noticed in [moirai/issues/1](https://github.com/csiro-hydroinformatics/moirai/issues/1), rather than `refcount` _per se_.

## [v1.2.5](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.2.5) - 2024-11-01

<small>[Compare with v1.2.0](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v1.2.0...v1.2.5)</small>

* Support wrapper generation with 4 parameter constructors for backward compat with swift wrappers.
* cumulative dependency updates
* increased unit test coverage

## [v1.2.0](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.2.0) - 2023-01-25

<small>[Compare with v1.1.1](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v1.1.1...v1.2.0)</small>

### Build

`wrap_as_pointer_handle` wraps `None` via a `GenericWrapper`, to facilitate code generation on top of a C API allowing `nullptr` to be passed in.


## [v1.1.1](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.1.1) - 2022-08-19

<small>[Compare with v1.1.0](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v1.1.0...v1.1.1)</small>

### Build

Minor changes that may not have been required to build the [conda package](https://github.com/conda-forge/refcount-feedstock/pull/2)

## [v1.1.0](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.1.0) - 2022-08-19

<small>[Compare with v1.0.0](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v1.0.0...v1.1.0)</small>

### Build

* Expand some features to cater for macos
* Tidy up and reengineer some of the legacy functions in the platform utilities `putils` to facilitate library loading. Minor breaking changes, but probably for no-one but the author in effect.

## [v1.0.0](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v1.0.0) - 2022-08-13

<small>[Compare with v0.9.3](https://github.com/csiro-hydroinformatics/pyrefcount/compare/v0.9.3...v1.0.0)</small>

### Build

* Improve documentation, and use the mkdocs-material theme
* mkdocs.yml changes. Enable dark/light modes from mkdocs-material
* Improved type hints, and add static type checks (mypy)
* Improve unit tests and add unit test code coverage reporting
* Manage the package using poetry; phase out setuptools.
* Apply some of the approaches in https://py-pkgs.org.
* Restore appveyor CI to a working state

## [v0.9.3](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/v0.9.3) - 2022-01-24

<small>[Compare with 0.9.1](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.9.1...v0.9.3)</small>

### Feature

* Add a class CffiWrapperFactory

## [0.9.1](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.9.1) - 2021-04-07

<small>[Compare with 0.9](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.9...0.9.1)</small>

## [0.9](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.9) - 2021-03-09

<small>[Compare with 0.8](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.8...0.9)</small>

## [0.8](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.8) - 2021-01-11

<small>[Compare with 0.6.2](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.6.2...0.8)</small>

## [0.6.2](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.6.2) - 2019-01-03

<small>[Compare with 0.6.0](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.6.0...0.6.2)</small>

## [0.6.0](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.6.0) - 2019-01-02

<small>[Compare with 0.5.1](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.5.1...0.6.0)</small>

## [0.5.1](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.5.1) - 2018-12-19

<small>[Compare with 0.5](https://github.com/csiro-hydroinformatics/pyrefcount/compare/0.5...0.5.1)</small>

## [0.5](https://github.com/csiro-hydroinformatics/pyrefcount/releases/tag/0.5) - 2018-12-19

<small>[Compare with first commit](https://github.com/csiro-hydroinformatics/pyrefcount/compare/3bd3f85c8cb55205c986a138c0b3806f711e05ad...0.5)</small>
