# ClickHouse Java Skills

Cursor Agent Skills for working with the ClickHouse Java client (`com.clickhouse:client-v2`). These skills help upgrade dependencies and configure the client for different use cases.

## Skills

### clickhouse-client-upgrade

Upgrades the ClickHouse Java client to the latest version **within the same major version**. Before applying changes, it:

- Discovers the current version from Gradle or Maven
- Fetches available versions from Maven Central
- Selects the highest patch/minor within the same major (e.g., `0.9.0` → `0.9.6`, not `0.10.0`)
- Fetches and parses the changelog from GitHub
- Categorizes changes by **risk** (High, Medium, Low) and **area** (Client API, JDBC, Dependencies)
- Produces an upgrade summary, then applies the upgrade

**Use when**: Upgrading the ClickHouse client, checking client-v2 versions, or reviewing the changelog before a dependency update.

**Helper script**: `.cursor/skills/clickhouse-client-upgrade/scripts/upgrade_check.py` — automates discovery, version selection, and summary generation.

### clickhouse-client-v2-configure

Configures `Client.Builder` and operation settings (`QuerySettings`, `InsertSettings`) for specific use cases. It:

- Asks for the target class/method and use case
- Applies appropriate settings (buffers, timeouts, compression)
- Documents decisions in code comments

**Use cases**:

| Category | Description |
|----------|-------------|
| Fetch small | Few records, low latency (lookups, dashboards) |
| Fetch big batches | Large result sets; memory and throughput matter |
| Insert small | &lt;100k records per batch; transactional or micro-batch loads |
| Insert big batches | Large bulk inserts; memory, network buffers, timeouts, compression |

**Use when**: Configuring client-v2, tuning for batch size, or optimizing for memory/throughput.

## Project Structure

```
.cursor/
├── skills/
│   ├── clickhouse-client-upgrade/
│   │   ├── SKILL.md
│   │   ├── reference.md
│   │   └── scripts/upgrade_check.py
│   └── clickhouse-client-v2-configure/
│       ├── SKILL.md
│       └── reference.md
└── commands/
    └── clickhouse-client-v2-configure.md
app/
└── src/main/java/...   # Sample application
```

## Requirements

- Gradle or Maven
- Python 3 (for `upgrade_check.py`)

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
