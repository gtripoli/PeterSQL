#!/bin/bash
# Local test runner (fast, excludes integration tests)
# For local development and pre-commit hooks
# Does NOT update badges - use runtest.sh for that

echo "Running local tests (excluding integration tests)..."

# Run all tests except integration tests (testcontainers)
# Integration tests are marked with @pytest.mark.integration
uv run pytest tests/ -m "not integration" --cov=. --cov-report=term --tb=short -v

PYTEST_EXIT_CODE=$?

echo ""
echo "Local tests completed. Exit code: $PYTEST_EXIT_CODE"
echo ""
echo "Note: Integration tests excluded. Run 'scripts/runtest.sh' for full test suite with badge updates."

exit $PYTEST_EXIT_CODE
