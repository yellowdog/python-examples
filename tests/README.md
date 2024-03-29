**Work in Progress**

# Placeholder

The tests in this directory are run using Pytest.

# Running Live Demos

The `--run-demos` flag is required to run the live demos.

# Parallel Testing

To run tests in parallel -- the demos for example, e.g.:

```shell
pytest -v -n 2 --run-demos -k 'bash or primes'
pytest -v -n 10 --run-demos -k demos
```
