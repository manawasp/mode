#!/usr/bin/env bash

set -e
set -x

pytest tests/unit tests/functional --cov=mode
