# building for unit tests

```sh
cmake -H. -Bbuild
cmake --build build -- -j3
```

The first command will creates CMake configuration files inside folder build and the second one will generate the output in bin folder