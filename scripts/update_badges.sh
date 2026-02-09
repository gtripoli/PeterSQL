#!/bin/bash
# Script to update version badges in README.md based on actual test results

README="README.md"
TESTS_DIR="tests/engines"

# Run tests for a specific engine and return color based on result
# green = all passed, red = all failed, orange = partial
run_engine_tests() {
    local engine=$1
    local test_path="$TESTS_DIR/$engine"
    
    if [ ! -d "$test_path" ]; then
        echo "red"
        return
    fi
    
    # Run tests and capture output
    output=$(uv run pytest "$test_path" --tb=no -q 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "green"
    elif echo "$output" | grep -q "passed"; then
        # Some passed, some failed
        echo "orange"
    else
        echo "red"
    fi
}

# Extract versions from conftest files and format for badge URL
extract_versions_badge() {
    local file=$1
    local var_name=$2
    # Extract versions, join with %20|%20 for URL encoding
    grep -A 10 "${var_name}.*=" "$file" 2>/dev/null | \
        grep -oP '"[^"]+:[^"]+"' | \
        tr -d '"' | \
        sed 's/.*://' | \
        grep -v '^$' | \
        sort -V | \
        paste -sd'|' | \
        sed 's/|/%20%7C%20/g'
}

# Extract versions for display
extract_versions_display() {
    local file=$1
    local var_name=$2
    grep -A 10 "${var_name}.*=" "$file" 2>/dev/null | \
        grep -oP '"[^"]+:[^"]+"' | \
        tr -d '"' | \
        sed 's/.*://' | \
        grep -v '^$' | \
        sort -V | \
        paste -sd' '
}

echo "Running tests to determine badge colors..."

# SQLite
echo -n "  SQLite: "
SQLITE_COLOR=$(run_engine_tests "sqlite")
echo "$SQLITE_COLOR"

# MySQL
echo -n "  MySQL: "
MYSQL_COLOR=$(run_engine_tests "mysql")
MYSQL_BADGE=$(extract_versions_badge "$TESTS_DIR/mysql/conftest.py" "MYSQL_VERSIONS")
MYSQL_DISPLAY=$(extract_versions_display "$TESTS_DIR/mysql/conftest.py" "MYSQL_VERSIONS")
echo "$MYSQL_COLOR ($MYSQL_DISPLAY)"

# MariaDB
echo -n "  MariaDB: "
MARIADB_COLOR=$(run_engine_tests "mariadb")
MARIADB_BADGE=$(extract_versions_badge "$TESTS_DIR/mariadb/conftest.py" "MARIADB_VERSIONS")
MARIADB_DISPLAY=$(extract_versions_display "$TESTS_DIR/mariadb/conftest.py" "MARIADB_VERSIONS")
echo "$MARIADB_COLOR ($MARIADB_DISPLAY)"

# PostgreSQL
echo -n "  PostgreSQL: "
POSTGRESQL_COLOR=$(run_engine_tests "postgresql")
POSTGRESQL_BADGE=$(extract_versions_badge "$TESTS_DIR/postgresql/conftest.py" "POSTGRESQL_VERSIONS")
POSTGRESQL_DISPLAY=$(extract_versions_display "$TESTS_DIR/postgresql/conftest.py" "POSTGRESQL_VERSIONS")
echo "$POSTGRESQL_COLOR ($POSTGRESQL_DISPLAY)"

# Update README badges with colors using perl for safer regex
perl -i -pe "s|!\[SQLite\]\(https://img.shields.io/badge/SQLite-[^)]*\)|![SQLite](https://img.shields.io/badge/SQLite-tested-${SQLITE_COLOR})|g" "$README"
perl -i -pe "s|!\[MySQL\]\(https://img.shields.io/badge/MySQL-[^)]*\)|![MySQL](https://img.shields.io/badge/MySQL-${MYSQL_BADGE}-${MYSQL_COLOR})|g" "$README"
perl -i -pe "s|!\[MariaDB\]\(https://img.shields.io/badge/MariaDB-[^)]*\)|![MariaDB](https://img.shields.io/badge/MariaDB-${MARIADB_BADGE}-${MARIADB_COLOR})|g" "$README"
perl -i -pe "s|!\[PostgreSQL\]\(https://img.shields.io/badge/PostgreSQL-[^)]*\)|![PostgreSQL](https://img.shields.io/badge/PostgreSQL-${POSTGRESQL_BADGE}-${POSTGRESQL_COLOR})|g" "$README"

echo ""
echo "README.md badges updated."
