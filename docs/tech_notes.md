# refcount tech notes

**These are notes for the package maintainer(s)**. Most users can ignore them.

Note to self: as of Jan 2019 also using github_jm\didactique\doc\know_how.md to log the exploratory and release processes around `refcount`

## Poetry

2023-04

```sh
cd ~/src/pyrefcount
```

[https://py-pkgs.org](https://py-pkgs.org)

```sh
mamba env list
mamba create -n poetry python=3.9 poetry
```

## Release steps

* all UT pass
* Merge new features/fixes to devel branch.
* version.py updated
* check readme is up to date

```sh
mamba activate poetry
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
