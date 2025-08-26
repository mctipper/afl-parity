#!/bin/bash

# exit status so other scripts can hook into this output (not implemented...)
exit_status=0

echo "Running ruff to check for linting issues..."
/home/vscode/.venv/bin/ruff check
if [ $? -ne 0 ]; then
    exit_status=1
fi

echo ""

echo "Running ruff to format the code..."
/home/vscode/.venv/bin/ruff format
if [ $? -ne 0 ]; then
    exit_status=1
fi

echo ""

echo "Running mypy to check for type errors..."
/home/vscode/.venv/bin/mypy .
if [ $? -ne 0 ]; then
    exit_status=1
fi



exit $exit_status
