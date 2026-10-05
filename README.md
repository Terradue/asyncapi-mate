# AsyncAPI Mate

[![PyPI - Version](https://img.shields.io/pypi/v/asyncapi-mate.svg)](https://pypi.org/project/asyncapi-mate)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/asyncapi-mate.svg)](https://pypi.org/project/asyncapi-mate)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Terradue/asyncapi-mate/package.yaml?branch=develop&event=push&label=build&logo=githubactions)](https://github.com/Terradue/asyncapi-mate/actions/workflows/package.yaml?query=branch%3Adevelop)
[![Code coverage](https://img.shields.io/codecov/c/github/Terradue/asyncapi-mate/develop?logo=codecov)](https://app.codecov.io/gh/Terradue/asyncapi-mate/tree/develop)

This repository contains the Python tooling for the SEDA Markdown template project.

## Development

Create and enter the default Hatch environment:

```bash
hatch shell
```

If your environment restricts writes to the home cache, point Hatch to a writable cache first:

```bash
XDG_CACHE_HOME=$PWD/.cache HATCH_DATA_DIR=$PWD/.hatch hatch shell
```

## License

[![Apache License, Version 2.0](https://img.shields.io/badge/license-Apache%20License%202.0-blue)](https://www.apache.org/licenses/LICENSE-2.0)
