#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running UBID pipeline to generate initial data..."
python -m src.main

echo "Build complete!"
