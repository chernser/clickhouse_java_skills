# Configure ClickHouse client-v2

Use the **clickhouse-client-v2-configure** skill to configure the ClickHouse Java client for the specified class or method.

1. Read `.cursor/skills/clickhouse-client-v2-configure/SKILL.md` and follow its workflow.
2. Ask the user: which class or method to configure, and what use case (fetch small, fetch big batches, insert small &lt;100k, insert big batches).
3. Apply the appropriate settings from `.cursor/skills/clickhouse-client-v2-configure/reference.md`.
4. Add inline comments explaining each setting.
5. Verify the build.
