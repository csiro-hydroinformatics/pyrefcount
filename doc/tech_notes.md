# refcount tech notes

Note to self: as of Jan 2019 also using github_jm\didactique\doc\know_how.md to log the exploratory and release processes around `refcount`

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
conda install  wheel twine six pytest
```

```sh
conda activate ${my_env_name}
cd ~/src/github_jm/pyrefcount
rm dist/*
python3 setup.py sdist bdist_wheel
rm dist/*.tar
twine upload dist/*
```
