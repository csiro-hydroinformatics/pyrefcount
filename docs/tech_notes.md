# refcount tech notes

**These are notes for the package maintainer(s)**. Most users can ignore them.

## History

* Migrated to use poetry 2023-04 after reading [https://py-pkgs.org](https://py-pkgs.org), poetry grated but got over it. 
* Jan 2025. poetry 2.0, Significant changes to the pyproject toml.
  * installing poetry via pipx.
  * BUT had started a branch for packaging with `uv`. Time to move on anyway.
  * Trialing package development using [this `copier-uv`template](https://pawamoy.github.io/copier-uv/work/). Note also the [blog post from Simon Wilson on uv](https://til.simonwillison.net/python/uv-cli-apps)


```sh
cd ~/src/pyrefcount
```

## Release steps

* all UT pass
* Merge new features/fixes to devel branch.
* version.py updated
* check readme is up to date

```sh
poetry install
poetry version
pytest tests/
```

Not sure about using poetry for repos push.

```sh
poetry config repositories.test-pypi https://upload.pypi.org/legacy/
```

with `.pypirc` configured:

```sh
rm dist/*
poetry build
ls dist/

twine upload -r testpypi dist/*
# check
twine upload -r pypi dist/*

```

## Code - deprecated

```sh
cd ~/src/github_jm/pyrefcount
```

```sh
source ~/anaconda3/bin/activate
my_env_name=testpypirefcount
```

```sh
conda create --name ${my_env_name} python=3.6
conda activate ${my_env_name}
conda install -c conda-forge wheel twine six pytest
```

```sh
conda activate ${my_env_name}
cd ~/src/github_jm/pyrefcount
rm dist/*
python setup.py sdist bdist_wheel
rm dist/*.tar
```

Importantly to not end up with incorrect display of the readme:

```sh
twine check dist/*
```

```sh
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

Then and only then:

```sh
twine upload dist/*
```

## Documentation

2021-01 Exploring options for putting this on readthedoc. I used in the past sphinx with napoleon extensions to document [ela](https://pyela.readthedocs.io/en/latest). This was a trial run. Did something more substantial for an internal project (WAA).

Starting afresh with this, reading the RTD guides. Introduces mkdocs. Notice [this blog on mkdocs-material](https://chrieke.medium.com/documenting-a-python-package-with-code-reference-via-mkdocs-material-b4a45197f95b) which seems like the new cool kid on the block.

Unclear from RTD where to create a new mkdocs project (supposed to be in the root of the python package?) not sure. for now:

```sh
cd doc
mkdir mkd
cd mkd/
mkdocs new .
```

`mamba install -c conda-forge mkdocs-material mkdocstrings`
`mamba install -c conda-forge mkdocs-material-extensions`

Building the doc:

```sh
. ~/config/baseconda
conda activate poetry
mkdocs build --clean --site-dir _build/html --config-file mkdocs.yml
mkdocs serve
```

## testing

```sh
# pytest tests/ --cov=refcounts # generates a warning about no coverage data cvollected
coverage run -m pytest
# pytest --cov=refcounts --cov-report html
coverage report
coverage html -d coverage_html
```

## Troubleshooting

OUTDATED no more rst.

```sh
pandoc -f markdown -t rst README.md  > README.rst
```

Can view with the `retext` program (did not find VScode RST extensions working, or giving out blank output if not, perhaps)

```sh
python setup.py check --restructuredtext
```
