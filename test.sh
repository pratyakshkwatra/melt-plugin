#!/bin/bash
echo "Setting up Python Virtual Environment for Testing..."
python3 -m venv .venv
source .venv/bin/activate
echo "Installing dependencies..."
pip install --upgrade pip
pip install pytest mock requests flask msgpack-python
echo "Running PyTest Suite..."
pytest tests/
