Here you can find mocked implementations of third party contracts e.g. Folks lending pools. The mocked contracts are used in automated tests.

The contracts are written in [Tealish](https://tealish.tinyman.org).

**To compile a specific contract run**:

```
poetry run tealish compile contract-mocks/folks_lending_pool_mock.tl
```

The generated `.teal` files will be stored in `contract-mocks/build` directory.
