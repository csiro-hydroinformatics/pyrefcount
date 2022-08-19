# Changelog

<!--next-version-placeholder-->

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
