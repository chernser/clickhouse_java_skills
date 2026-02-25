---
name: clickhouse-client-v2-configure
description: Configures ClickHouse Java client-v2 (Client.Builder) for specific use cases. Asks user about use case, then applies appropriate settings (buffers, timeouts, compression) to the specified class or method. Use when configuring client-v2, tuning for batch size, or optimizing ClickHouse client for memory/throughput.
---

# ClickHouse Client-v2 Configuration

## Overview

Configures `com.clickhouse.client.api.Client.Builder` and operation settings (`QuerySettings`, `InsertSettings`) for ClickHouse Java client-v2. The skill **scopes changes to a user-specified class or method** and documents decisions in code comments.

## Workflow

### Step 1: Ask for scope and use case

**Scope**: Which class or method should be configured? (e.g., `ClientFactory.create()`, `DataLoader.loadBatch()`)

**Use case** (pick one):

| Category | Description |
|----------|-------------|
| **Fetch small** | Few records, low latency (e.g., lookups, dashboards) |
| **Fetch big batches** | Large result sets for extraction/ETL; memory and throughput matter |
| **Insert small** | &lt;100k records per batch; typical transactional or micro-batch loads |
| **Insert big batches** | Large bulk inserts; memory pressure, network buffers, timeouts, compression |

If the user does not specify, ask: *"What is the primary use case for this client: fetching small records, fetching big batches, inserting small batches (&lt;100k), or inserting big batches?"*

### Step 2: Locate the target code

Search only within the specified class or method for:

- `Client.Builder` / `new Client.Builder()`
- `QuerySettings` / `InsertSettings`
- `client.query(...)` / `client.insert(...)`

Do **not** modify code outside the specified scope.

### Step 3: Apply configuration by use case

Use the recommendations in [reference.md](reference.md). Add configuration via Builder methods and operation settings. Document each non-default choice with a short comment.

### Step 4: Document decisions in comments

For every applied setting, add an inline comment explaining why (e.g., use case or constraint):

```java
return new Client.Builder()
        .addEndpoint(endpoint)
        .setUsername(username)
        .setPassword(password)
        // Big-batch inserts: larger network buffer to reduce memory churn
        .setClientNetworkBufferSize(4 * 1024 * 1024)
        // Big-batch inserts: allow long-running inserts to complete
        .setExecutionTimeout(30, ChronoUnit.MINUTES)
        .compressClientRequest(true)  // Reduce transfer size for large payloads
        .build();
```

### Step 5: Verify build

Run `./gradlew build` or `mvn compile` to ensure the project still builds.

## Use Case Summary

| Use case | Key concerns | Main settings |
|----------|---------------|---------------|
| Fetch small | Low latency, defaults usually fine | Optional: `setSocketTimeout`, `setConnectTimeout` |
| Fetch big batches | Memory, throughput | `setClientNetworkBufferSize`, `setSocketTimeout`, `compressServerResponse`, streaming (avoid `queryAll` for huge results) |
| Insert small | Simplicity | Defaults or light tuning; optional `compressClientRequest` |
| Insert big batches | **Memory**, network buffers, timeouts, compression | `setClientNetworkBufferSize`, `setSocketRcvbuf`/`setSocketSndbuf`, `setExecutionTimeout`, `compressClientRequest(true)`, `InsertSettings.setInputStreamCopyBufferSize` |

## Big-batch memory warning

For **insert big batches** and **fetch big batches**, convey to the user:

- Large batches increase memory usage on both client and server.
- Use **streaming** where possible (e.g., `InputStream` for inserts, `QueryResponse` + reader for queries) instead of loading everything into memory.
- Increase network buffers (`setClientNetworkBufferSize`, `setSocketRcvbuf`, `setSocketSndbuf`) so fewer smaller buffers are allocated.
- Set **reasonable timeouts** (`setExecutionTimeout`, `setSocketTimeout`) so long operations do not fail prematurely.
- Enable **compression** (`compressClientRequest` for inserts, `compressServerResponse` for queries) to reduce transfer size and often memory pressure.

## Additional Resources

- Configuration options by use case: [reference.md](reference.md)
- Client API docs: https://clickhouse.com/docs/integrations/language-clients/java/client
