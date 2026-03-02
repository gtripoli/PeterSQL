# Versioning Policy

## 1. Purpose

This document defines how to bump versions for any project or
repository. If a repository requires different rules, it **MUST**
explicitly define a local override document.

------------------------------------------------------------------------

## 2. Version Format

All projects **MUST** use the following format:

    MAJOR.MINOR.PATCH

Optional pre-release suffix:

    -alpha.N
    -beta.N
    -rc.N

### Examples

    1.4.2
    2.0.0-rc.1
    0.5.0-alpha.3

------------------------------------------------------------------------

## 3. Bump Rules

### 3.1 PATCH (x.y.Z)

Use PATCH for backward-compatible bug fixes and safe internal
improvements that do **NOT** change public behavior or contracts.

#### Good examples

    1.0.0 → 1.0.1  (bug fix)
    1.2.3 → 1.2.4  (security fix)
    2.4.1 → 2.4.2  (internal refactor without behavior change)

#### Bad examples

    1.2.3 → 1.2.4  while changing API response schema
    1.2.3 → 1.2.4  while removing a feature

------------------------------------------------------------------------

### 3.2 MINOR (x.Y.0)

Use MINOR for backward-compatible feature additions.

#### Good examples

    1.0.1 → 1.1.0  (new optional feature)
    2.3.4 → 2.4.0  (new endpoint, old clients still work)
    3.2.5 → 3.3.0  (new configuration option, not required)

#### Bad examples

    1.2.0 → 1.3.0  if existing clients break
    1.2.0 → 1.3.0  when default behavior changes incompatibly

------------------------------------------------------------------------

### 3.3 MAJOR (X.0.0)

Use MAJOR for breaking changes.

A change is breaking if it may require modifications in consumers.

#### Good examples

    1.4.3 → 2.0.0  (breaking API change)
    2.1.0 → 3.0.0  (removed feature)
    3.5.2 → 4.0.0  (database schema incompatible change)
    5.0.0 → 6.0.0  (default behavior changed incompatibly)

#### Bad examples

    1.4.3 → 2.0.0  for a simple bug fix
    1.4.3 → 2.0.0  for adding an optional feature

------------------------------------------------------------------------

## 4. Reset Rules (Mandatory)

When bumping:

-   MAJOR → reset MINOR and PATCH to 0
-   MINOR → reset PATCH to 0
-   PATCH → no reset required

#### Good examples

    1.0.1 → 1.1.0
    1.1.9 → 2.0.0
    2.3.4 → 2.3.5

#### Forbidden by policy

    1.0.1 → 1.1.2
    1.2.3 → 2.1.0

Correct sequence:

    1.0.1 → 1.1.0 → 1.1.1 → 1.1.2

------------------------------------------------------------------------

## 5. Pre-1.0.0 Versions (0.x.y)

Before 1.0.0, breaking changes are expected more frequently.

### Recommended behavior

-   Breaking change → bump MINOR (0.3.4 → 0.4.0)
-   Bug fix → bump PATCH (0.3.4 → 0.3.5)

### Pre-release usage

    0.4.0-alpha.1  → early unstable version
    0.4.0-beta.1   → feature-complete preview
    0.4.0-rc.1     → release candidate, only bug fixes allowed

Nightly builds **SHOULD** use `-alpha.N` (or `-dev.N`) and **MUST NOT**
be published as stable releases.

------------------------------------------------------------------------

## 6. Breaking Change Definition

A change is breaking if it can require changes in consumers, including:

-   Public API modification
-   Response structure change
-   Configuration requirement change
-   Removed functionality
-   Default behavior change
-   Schema incompatibility
-   Environment variable changes (new required vars, renamed/removed
    vars)

### Desktop / PyInstaller-specific breaking changes

Also considered breaking:

-   Configuration directory changes without migration
-   Workspace/session schema changes without backward compatibility
-   Removed or renamed CLI flags
-   Removed or renamed required resource files (themes, templates, etc.)

If in doubt, treat the change as breaking and bump MAJOR (or MINOR in
0.x.y).

------------------------------------------------------------------------

## 7. No Skipping Rule

Versions **MUST** follow logical semantic transitions.

#### Good examples

    1.2.3 → 1.2.4
    1.2.4 → 1.3.0
    1.3.0 → 2.0.0

#### Forbidden by policy

    1.2.3 → 1.4.7
    1.0.1 → 1.1.2 (without intermediate steps)

All increments **MUST** be semantically justified.
