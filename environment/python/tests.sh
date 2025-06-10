#!/bin/bash

TEST_PATH=${1:-"tests"}

#coverage run --omit="*/tests/*" -m unittest discover -s "$TEST_PATH" -v
#coverage html

pytest --cov=src --cov-report=html "$TEST_PATH" -v