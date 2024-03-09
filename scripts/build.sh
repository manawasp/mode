#!/bin/sh -e

set -x

python3 -m build . --wheel
twine check dist/*
