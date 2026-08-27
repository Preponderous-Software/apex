#!/bin/bash
set -e

# Run unit tests with coverage
python3 -m pytest --cov=src --cov-report=xml tests
