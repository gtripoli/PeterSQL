#!/bin/bash
# Unified test runner with badge updates
# Runs all tests once and updates README badges based on results
# Replaces: pytest, update_coverage_badge, update_version_badges

README="README.md"
TESTS_DIR="tests/engines"
RESULTS_FILE="/tmp/pytest_results.txt"
COVERAGE_FILE="/tmp/pytest_coverage.txt"

echo "Running all tests with coverage..."

# Run all tests once with coverage, save results
uv run pytest tests/ -n auto --cov=. --cov-report=term --tb=no -v 2>&1 | tee "$RESULTS_FILE"
PYTEST_EXIT_CODE=${PIPESTATUS[0]}

# Extract coverage percentage
COVERAGE=$(grep "TOTAL" "$RESULTS_FILE" | awk '{print $4}' | sed 's/%//' | head -1)
echo ""
echo "Coverage: ${COVERAGE}%"

echo ""
echo "Analyzing results for badge updates..."

# Function to determine color from test results
get_engine_color() {
    local engine=$1
    local pattern="tests/engines/${engine}/"
    
    # Count passed and failed for this engine
    local passed=$(grep -c "PASSED" "$RESULTS_FILE" | grep -c "$pattern" 2>/dev/null || echo 0)
    local failed=$(grep -c "FAILED" "$RESULTS_FILE" | grep -c "$pattern" 2>/dev/null || echo 0)
    
    # Check if any tests for this engine exist in results
    if grep -q "$pattern.*PASSED" "$RESULTS_FILE" 2>/dev/null; then
        if grep -q "$pattern.*FAILED" "$RESULTS_FILE" 2>/dev/null; then
            echo "orange"
        else
            echo "green"
        fi
    elif grep -q "$pattern.*FAILED" "$RESULTS_FILE" 2>/dev/null; then
        echo "red"
    else
        # No tests found for this engine
        echo "lightgrey"
    fi
}

# Extract versions from conftest files for badge URL
extract_versions_badge() {
    local file=$1
    local var_name=$2
    grep -A 10 "${var_name}.*=" "$file" 2>/dev/null | \
        grep -oP '"[^"]+:[^"]+"' | \
        tr -d '"' | \
        sed 's/.*://' | \
        grep -v '^$' | \
        sort -V | \
        paste -sd'|' | \
        sed 's/|/%20%7C%20/g'
}

# Determine colors from single test run
echo -n "  SQLite: "
SQLITE_COLOR=$(get_engine_color "sqlite")
echo "$SQLITE_COLOR"

echo -n "  MySQL: "
MYSQL_COLOR=$(get_engine_color "mysql")
MYSQL_BADGE=$(extract_versions_badge "$TESTS_DIR/mysql/conftest.py" "MYSQL_VERSIONS")
echo "$MYSQL_COLOR"

echo -n "  MariaDB: "
MARIADB_COLOR=$(get_engine_color "mariadb")
MARIADB_BADGE=$(extract_versions_badge "$TESTS_DIR/mariadb/conftest.py" "MARIADB_VERSIONS")
echo "$MARIADB_COLOR"

echo -n "  PostgreSQL: "
POSTGRESQL_COLOR=$(get_engine_color "postgresql")
POSTGRESQL_BADGE=$(extract_versions_badge "$TESTS_DIR/postgresql/conftest.py" "POSTGRESQL_VERSIONS")
echo "$POSTGRESQL_COLOR"

# Update README badges
if [ -f "$README" ]; then
    # Update coverage badge
    if [ -n "$COVERAGE" ]; then
        sed -i "s/coverage-[0-9]*%/coverage-${COVERAGE}%/g" "$README"
        echo "  Coverage badge updated: ${COVERAGE}%"
    fi
    
    # Update engine badges
    perl -i -pe "s|!\[SQLite\]\(https://img.shields.io/badge/SQLite-[^)]*\)|![SQLite](https://img.shields.io/badge/SQLite-tested-${SQLITE_COLOR})|g" "$README"
    perl -i -pe "s|!\[MySQL\]\(https://img.shields.io/badge/MySQL-[^)]*\)|![MySQL](https://img.shields.io/badge/MySQL-${MYSQL_BADGE}-${MYSQL_COLOR})|g" "$README"
    perl -i -pe "s|!\[MariaDB\]\(https://img.shields.io/badge/MariaDB-[^)]*\)|![MariaDB](https://img.shields.io/badge/MariaDB-${MARIADB_BADGE}-${MARIADB_COLOR})|g" "$README"
    perl -i -pe "s|!\[PostgreSQL\]\(https://img.shields.io/badge/PostgreSQL-[^)]*\)|![PostgreSQL](https://img.shields.io/badge/PostgreSQL-${POSTGRESQL_BADGE}-${POSTGRESQL_COLOR})|g" "$README"
    
    # Stage README for commit
    git add "$README"
    
    echo ""
    echo "README.md badges updated and staged."
fi

# Cleanup
rm -f "$RESULTS_FILE"

echo ""
echo "Done. Pytest exit code: $PYTEST_EXIT_CODE"

# Exit with original pytest exit code
exit $PYTEST_EXIT_CODE
