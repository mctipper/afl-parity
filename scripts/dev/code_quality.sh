#!/bin/bash

# exit status so other scripts can hook into this output (not implemented...)
exit_status=0

echo "Running mypy to check for type errors..."
mypy .
if [ $? -ne 0 ]; then
    exit_status=1
fi

echo ""

echo "Running ruff to check for linting issues..."
ruff check
if [ $? -ne 0 ]; then
    exit_status=1
fi

echo ""

echo "Running ruff to format the code..."
ruff format
if [ $? -ne 0 ]; then
    exit_status=1
fi

exit $exit_status
