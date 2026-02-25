# Risk and Area Categorization

## Risk Levels

| Risk | Changelog Sections | Examples |
|------|-------------------|----------|
| **High** | Dependencies (CVE/vuln), Important Changes | CVE fixes, removed artifacts, breaking API changes |
| **Medium** | Bug Fixes | Behavior fixes, backward compatibility, connection leaks |
| **Low** | New Features, Improvements, Misc, Docs | New methods, logging format, documentation |

### High Risk Indicators

- CVE references, vulnerability, security
- "upgraded X to Y. Previously used version had a vulnerability"
- "not published anymore", "Use X instead"
- "Important Changes" section
- Removed or renamed artifacts

### Medium Risk Indicators

- "Fixed" in description
- "backward compatibility"
- "connection leaking", "NPE", "exception handling"
- Behavior changes that could affect existing code

### Low Risk Indicators

- "Added", "Added support for"
- "Improved", "Improved handling"
- "Misc", "Docs"
- New optional features, logging format changes

## Area Mapping

| Changelog Tag | Area Name | Scope |
|---------------|-----------|-------|
| `[client-v2]` | Client API | Native HTTP client, `ClickHouseClient`, data types |
| `[jdbc-v2]` | JDBC Driver | JDBC API, prepared statements, ResultSet |
| `[repo]` | Dependencies | Transitive deps, build artifacts, CVE upgrades |
| `[client-v1]` | Legacy Client | Old HTTP client (deprecated) |

## Version Parsing

- **Release versions**: `0.9.0`, `0.9.6`, `0.8.6` — use for upgrade selection
- **Exclude from selection**: `0.6.0-patch5`, `0.7.1-patch1`, `*-SNAPSHOT`, `*-rc*`
- **Major version**: First two components for `0.x.y` (e.g., `0.9` from `0.9.6`)
