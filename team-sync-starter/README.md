# Team Sync Starter (Trino ⇄ MySQL ⇄ Hive Metastore)

A minimal, production-lean starter using **Java 24 + Javalin** with:
- Trino JDBC (Kerberos-capable)
- Hive Metastore Thrift client (Kerberos-capable)
- MySQL/MariaDB JDBC (password + optional GSSAPI mode)
- Static HTML to render Trino rows
- Static Swagger UI backed by `openapi.yaml`
- Orchestrator that:
  1. Reads rows from Trino (expects columns: `id`, `producer_team`, `consumer_team`).
  2. Uses `producer_team` to pull a full row from the producer team's MySQL table.
  3. Inserts that row into the consumer team's MySQL table (schema/table per team config).
  4. Optionally emails a summary.

> Everything is config-driven via YAML in `config/`.

## Quick start

```bash
# Java 24 + Maven required
mvn -q -e -DskipTests package

# Run
java -jar target/team-sync-0.1.0-shaded.jar
```

- UI: http://localhost:8080/ui
- Swagger: http://localhost:8080/swagger (loads `openapi.yaml`)

## Configure

Edit `config/application.yaml` and `config/teams.yaml`. Kerberos examples are provided (ticket cache / keytab).
You can point to custom `krb5.conf` and `jaas.conf`, or rely on OS defaults.

### Trino
- Set `trino.jdbcUrl` (include `SSL=true` and Kerberos props if applicable).
- If using Kerberos, ensure a valid TGT (ticket) exists, or set `principal/keytab` and `useTicketCache` accordingly.

### Hive Metastore
- Set `hms.uris: "thrift://host:9083"` and Kerberos flags if needed.

### MySQL/MariaDB per team
Each team entry provides:
- `driver`: `mysql` or `mariadb`
- `mode`: `PASSWORD` or `KERBEROS_GSSAPI`
- `url`, `user`, `password` (for password mode)
- For Kerberos/GSSAPI, set `gssService` and optionally `extras` map with driver-specific flags.

> NOTE: MySQL Community JDBC does **not** support Kerberos. If you truly need GSSAPI, use MariaDB server/driver with GSSAPI enabled, or your enterprise MySQL distribution that supports it, or a proxy that terminates Kerberos.

### Orchestrator assumptions
- Trino table rows include: `id`, `producer_team`, `consumer_team`.
- For a given team:
  - Producer table name = `teams[].tables.producerTable`
  - Consumer table name = `teams[].tables.consumerTable`
- The producer and consumer tables should share compatible columns (the insert uses producer columns).

### Email
Toggle via `email.enabled`. Configure SMTP host, port, creds, from, to.

## Kerberos
Examples are included in `config/jaas.conf` and `config/krb5.conf`. Set environment variables accordingly, e.g.:
```bash
export KRB5_CONFIG=$(pwd)/config/krb5.conf
export KRB5CCNAME=/tmp/krb5cc_myuser   # if using ticket cache
```

## Extend
- Add transformations between producer and consumer rows in `WiringService#transformRow`.
- Add more endpoints in `api/` and document them in `src/main/resources/swagger/openapi.yaml`.

---

**Security note:** This is a starter; harden for production (TLS, secrets management, input validation, SQL injection protection, etc.).
