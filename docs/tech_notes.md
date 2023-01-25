# refcount tech notes

**These are notes for the package maintainer(s)**. Most users can ignore them.

Note to self: as of Jan 2019 also using github_jm\didactique\doc\know_how.md to log the exploratory and release processes around `refcount`

## Poetry

2022-12

Having to update dependent package versions [GitPython vulnerable to Remote Code Execution due to improper user input validation](https://github.com/csiro-hydroinformatics/pyrefcount/security/dependabot/4). It is probably not a burning issue given this should be only a dev-time dependency and certainly not runtime (otherwise poetry is crap)

```sh
cd ~/src/pyrefcount
poetry --version # in a conda env for poetry...
```

`ModuleNotFoundError: No module named 'importlib_metadata'`. Right...

```sh
cd ~/bin
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj micromamba
micromamba shell init -s bash -p ~/micromamba
```

```sh
source ~/.bashrc
alias mm=micromamba
mm create -n poetry python=3.9
mm activate poetry
mm list
```

`pip install poetry`

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
plantuml-markdown 3.6.3 requires Markdown, which is not installed.
```

Huh??

`pip install Markdown` seems to fix it. Odd.

poetry --version returns 1.3.1 which seems to be what is available from conda-forge anyway. So:

```
mm deactivate
mm env remove -n poetry

mm create -n poetry python=3.9 poetry=1.3.1
mm activate poetry
mm list
```

## Release steps

* all UT pass
* Merge new features/fixes to devel branch.
* version.py updated
* check readme is up to date

## Code

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

