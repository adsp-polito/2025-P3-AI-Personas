#!/bin/bash
# Simple test runner script

set -e

echo "=== Running AI Personas Tests ==="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found"
    echo "Install it with: pip install pytest"
    exit 1
fi

# Default options
VERBOSE=""
COVERAGE=""
PATTERN=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -c|--coverage)
            COVERAGE="--cov=adsp --cov-report=term-missing"
            shift
            ;;
        -k)
            PATTERN="-k $2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-v|--verbose] [-c|--coverage] [-k pattern]"
            exit 1
            ;;
    esac
done

# Run tests
echo "Running pytest..."
pytest $VERBOSE $COVERAGE $PATTERN tests/

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
else
    echo ""
    echo "✗ Some tests failed"
    exit 1
fi
