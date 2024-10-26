# Nakamap: IMAS IDS mapping methods for JT-60SA data

[![image](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.13-blue)](https://git.iter.org/projects/EQ/repos/nova)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)

Nakamap helps you map JT-60SA data to IMAS IDSs using DDv4

## Installation
Installation is recomended using the Poetry environment.

The use of virtual environments is encoraged.

Installation on the Naka analysis server requires pre-installed version of IMASPy >= 1.1.0.
```sh
module use /home/d230021/public/imas/etc/modules/all
ml IMASPy

python -m venv ~/.venv/<venv_name>
. ~/.venv/<venv_name>/bin/activate
```

## Development
This packaging and development is managed using Poetry >= 2.

```sh
pipx install git+https://github.com/python-poetry/poetry.git
pipx inject poetry "git+https://github.com/mtkennerly/poetry-dynamic-versioning.git"

poetry install
pre-commit install
```
