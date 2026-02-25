package com.example.app;

import java.time.temporal.ChronoUnit;

import com.clickhouse.client.api.Client;

/**
 * Factory for creating ClickHouse client instances.
 * Configured for small-batch use (few records, low latency; e.g. lookups, dashboards, micro-batch inserts &lt;100k).
 */
public final class ClientFactory {

    private ClientFactory() {
    }

    /**
     * Creates a ClickHouse client with the default endpoint (http://localhost:8123).
     *
     * @return a new ClickHouse client instance
     */
    public static Client create() {
        return new Client.Builder()
                .addEndpoint("http://localhost:8123")
                // Small batches: fail fast if connection cannot be established
                .setConnectTimeout(5, ChronoUnit.SECONDS)
                // Small batches: quick failure detection for low-latency operations
                .setSocketTimeout(10, ChronoUnit.SECONDS)
                // Small batches: reduce transfer size for inserts
                .compressClientRequest(true)
                .build();
    }

    /**
     * Creates a ClickHouse client with the given endpoint.
     *
     * @param endpoint the server endpoint URL (e.g. "https://host:8443/")
     * @return a new ClickHouse client instance
     */
    public static Client create(String endpoint) {
        return new Client.Builder()
                .addEndpoint(endpoint)
                // Small batches: fail fast if connection cannot be established
                .setConnectTimeout(5, ChronoUnit.SECONDS)
                // Small batches: quick failure detection for low-latency operations
                .setSocketTimeout(10, ChronoUnit.SECONDS)
                // Small batches: reduce transfer size for inserts
                .compressClientRequest(true)
                .build();
    }

    /**
     * Creates a ClickHouse client with endpoint and credentials.
     *
     * @param endpoint the server endpoint URL
     * @param username the username for authentication
     * @param password the password for authentication
     * @return a new ClickHouse client instance
     */
    public static Client create(String endpoint, String username, String password) {
        return new Client.Builder()
                .addEndpoint(endpoint)
                .setUsername(username)
                .setPassword(password)
                // Small batches: fail fast if connection cannot be established
                .setConnectTimeout(5, ChronoUnit.SECONDS)
                // Small batches: quick failure detection for low-latency operations
                .setSocketTimeout(10, ChronoUnit.SECONDS)
                // Small batches: reduce transfer size for inserts
                .compressClientRequest(true)
                .build();
    }
}
