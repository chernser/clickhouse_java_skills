---
name: clickhouse-client-upgrade
description: Updates ClickHouse Java client dependencies by checking Maven Central for versions, selecting the latest within the same major version, summarizing changelog changes by risk and area, and applying the upgrade. Use when upgrading ClickHouse client, checking client-v2 versions, or reviewing changelog before dependency update.
---

# ClickHouse Client Upgrade

## Overview

Upgrades the ClickHouse Java client (`com.clickhouse:client-v2`) to the latest version **within the same major version**. Produces a categorized summary of changes by risk and area before applying the upgrade.

**Version selection rule**: If current is `0.9.0` and latest on Maven is `0.10.0`, upgrade to `0.9.x` (highest available in 0.9.x), not `0.10.0`.

## Workflow

### Step 1: Discover current version

Locate the ClickHouse client version in the project:

- **Gradle**: Check `gradle/libs.versions.toml` for `clickhouse-java` or `gradle.properties`; or `build.gradle` / `build.gradle.kts` for `com.clickhouse:client-v2`
- **Maven**: Check `pom.xml` for `com.clickhouse` / `client-v2` dependency

### Step 2: Fetch available versions from Maven

Use `maven-metadata.xml` (complete version list). The Maven Search API returns limited results and omits patch versions within a major.

```bash
curl -sL "https://repo1.maven.org/maven2/com/clickhouse/client-v2/maven-metadata.xml" | grep -oP '<version>\K[^<]+'
```

Or run the helper script:

```bash
python .cursor/skills/clickhouse-client-upgrade/scripts/upgrade_check.py --versions-only
```

### Step 3: Determine target version

- Parse versions; ignore `-patchN`, `-SNAPSHOT`, `-rc` suffixes for release selection
- Extract major version from current (e.g., `0.9.0` → major `0.9`)
- Select the **highest version** with the same major (e.g., `0.9.6` if available, else `0.9.5`, etc.)
- If current equals target, report "Already at latest within major version" and stop

### Step 4: Fetch and parse changelog

Fetch CHANGELOG from GitHub:

```bash
curl -sL "https://raw.githubusercontent.com/ClickHouse/clickhouse-java/main/CHANGELOG.md"
```

Extract entries for versions between current (exclusive) and target (inclusive). Changelog format:

```
## X.Y.Z
### Section (Dependencies | New Features | Bug Fixes | Important Changes | Improvements | Misc | Docs)
- [area] description (link)
```

### Step 5: Categorize changes

For each change entry, assign:

**Risk** (see [reference.md](reference.md)):
- **High**: Security (CVE, dependency vulns), Important Changes (breaking, removed artifacts)
- **Medium**: Bug Fixes, backward compatibility changes
- **Low**: New Features, Improvements, Misc, Docs

**Area** (from `[tag]` in entry):
- `client-v2` → Client API
- `jdbc-v2` → JDBC Driver
- `repo` → Dependencies / Build
- `client-v1` → Legacy Client

### Step 6: Produce upgrade summary

Use this template:

```markdown
# ClickHouse Client Upgrade: {current} → {target}

## Summary
- **Current**: {current}
- **Target**: {target} (latest within major {major})
- **Versions skipped**: {list if any, e.g. 0.10.0}

## Changes by Risk

### High
- [Area] Description (link)

### Medium
- [Area] Description (link)

### Low
- [Area] Description (link)

## Changes by Area

### Client API (client-v2)
- [Risk] Description

### JDBC Driver (jdbc-v2)
- [Risk] Description

### Dependencies (repo)
- [Risk] Description
```

### Step 7: Apply upgrade

**Gradle (libs.versions.toml)**:
```toml
[versions]
clickhouse-java = "{target}"
```

**Gradle (build.gradle)**:
```groovy
implementation 'com.clickhouse:client-v2:{target}'
```

**Maven (pom.xml)**:
```xml
<dependency>
  <groupId>com.clickhouse</groupId>
  <artifactId>client-v2</artifactId>
  <version>{target}</version>
</dependency>
```

### Step 8: Verify

- Run tests: `./gradlew test` or `mvn test`
- Rebuild: `./gradlew build` or `mvn compile`

## Helper Script

The `upgrade_check.py` script automates discovery, version selection, and summary generation:

```bash
# Full upgrade check and summary (requires project root or --toml path)
python .cursor/skills/clickhouse-client-upgrade/scripts/upgrade_check.py

# With explicit version catalog
python .cursor/skills/clickhouse-client-upgrade/scripts/upgrade_check.py --toml gradle/libs.versions.toml

# Versions only
python .cursor/skills/clickhouse-client-upgrade/scripts/upgrade_check.py --versions-only

# Apply upgrade (updates libs.versions.toml)
python .cursor/skills/clickhouse-client-upgrade/scripts/upgrade_check.py --apply
```

## Additional Resources

- Risk and area categorization rules: [reference.md](reference.md)
- Maven Central: https://central.sonatype.com/artifact/com.clickhouse/client-v2
- Changelog: https://github.com/ClickHouse/clickhouse-java/blob/main/CHANGELOG.md
