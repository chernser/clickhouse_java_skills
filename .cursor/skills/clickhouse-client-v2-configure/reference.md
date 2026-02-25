# ClickHouse Client-v2 Configuration by Use Case

## Builder Methods (Client Level)

| Method | Default | Use case | Typical value |
|--------|---------|----------|---------------|
| `setClientNetworkBufferSize(int)` | varies | Big fetch/insert | 4–16 MB (4*1024*1024) |
| `setSocketTimeout(long, ChronoUnit)` | varies | All | 30s–5min for big batches |
| `setConnectTimeout(long, ChronoUnit)` | varies | All | 10–30s |
| `setExecutionTimeout(long, ChronoUnit)` | varies | Big insert | 5–30 min |
| `setSocketRcvbuf(int)` | OS default | Big fetch/insert | 1–4 MB |
| `setSocketSndbuf(int)` | OS default | Big insert | 1–4 MB |
| `compressClientRequest(boolean)` | false | Insert (any size) | true for big batches |
| `compressServerResponse(boolean)` | false | Big fetch | true |
| `setMaxConnections(int)` | 10 | High concurrency | 20–50 |

## Operation Settings

### InsertSettings

| Method | Use case | Typical value |
|--------|----------|---------------|
| `setInputStreamCopyBufferSize(int)` | Big insert (streaming) | 64–256 KB (65536–262144) |

### QuerySettings

| Method | Use case | Notes |
|--------|----------|-------|
| `setFormat(ClickHouseFormat)` | Fetch | RowBinaryWithNamesAndTypes for binary streaming |
| `logComment(String)` | All | Identify operation in query log |

---

## Use Case: Fetch Small Records

**Profile**: Few rows, low latency (lookups, dashboards, API responses).

**Client.Builder**:
- Defaults usually sufficient.
- Optional: `setSocketTimeout(10, ChronoUnit.SECONDS)`, `setConnectTimeout(5, ChronoUnit.SECONDS)` for stricter failure detection.

**QuerySettings**:
- Default format fine.
- Optional: `logComment("lookup")` for observability.

---

## Use Case: Fetch Big Batches

**Profile**: Large result sets for ETL, exports, analytics. Memory and throughput matter.

**Client.Builder**:
```java
.setClientNetworkBufferSize(4 * 1024 * 1024)   // 4 MB
.setSocketTimeout(5, ChronoUnit.MINUTES)
.setSocketRcvbuf(1024 * 1024)                  // 1 MB
.compressServerResponse(true)
```

**QuerySettings**:
- Prefer streaming: use `client.query(sql)` + `ClickHouseBinaryFormatReader` instead of `queryAll()` to avoid loading the full result into memory.

**Memory note**: `queryAll()` loads the entire result set. For big batches, stream with `QueryResponse` and a reader.

---

## Use Case: Insert Small Batches (<100k records)

**Profile**: Transactional or micro-batch loads.

**Client.Builder**:
- Defaults usually sufficient.
- Optional: `compressClientRequest(true)` to reduce transfer size.

**InsertSettings** (when using `insert(table, InputStream, format, settings)`):
- Default `setInputStreamCopyBufferSize` is typically fine (e.g., 8–16 KB).

---

## Use Case: Insert Big Batches

**Profile**: Bulk loads. Memory pressure, network buffers, timeouts, and compression are important.

**Client.Builder**:
```java
.setClientNetworkBufferSize(4 * 1024 * 1024)   // 4 MB
.setSocketTimeout(5, ChronoUnit.MINUTES)
.setExecutionTimeout(30, ChronoUnit.MINUTES)
.setSocketRcvbuf(1024 * 1024)
.setSocketSndbuf(1024 * 1024)
.compressClientRequest(true)                   // LZ4; reduces transfer and often memory
```

**InsertSettings** (streaming insert):
```java
InsertSettings settings = new InsertSettings()
    .setInputStreamCopyBufferSize(256 * 1024);  // 256 KB copy buffer
```

**Memory considerations**:
- Prefer `insert(table, InputStream, format, settings)` over `insert(table, List)` to avoid holding all rows in memory.
- Use `InputStream` or chunked writes so data is streamed, not buffered entirely in the JVM.
- Compression reduces payload size and can lower memory usage during transfer.

**Timeout guidance**:
- `setExecutionTimeout`: 5–30 minutes depending on batch size and server load.
- `setSocketTimeout`: At least as long as the expected insert duration.
