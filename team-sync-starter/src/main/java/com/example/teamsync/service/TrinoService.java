package com.example.teamsync.service;

import com.example.teamsync.model.TrinoRow;
import com.example.teamsync.util.ConfigService;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

public class TrinoService {
    private final ConfigService.AppConfig config;
    private final KerberosAuth kerberos;

    public TrinoService(ConfigService.AppConfig config, KerberosAuth kerberos) {
        this.config = config;
        this.kerberos = kerberos;
    }

    public List<TrinoRow> readRows(String catalog, String schema, String table, int limit) {
        String url = rebuildUrlForCatalogSchema(config.trino().jdbcUrl(), catalog, schema);
        return withConnection(url, conn -> {
            String sql = "SELECT id, producer_team, consumer_team FROM " + table + " LIMIT " + limit;
            try (PreparedStatement ps = conn.prepareStatement(sql);
                 ResultSet rs = ps.executeQuery()) {
                List<TrinoRow> list = new ArrayList<>();
                while (rs.next()) {
                    list.add(new TrinoRow(
                            rs.getString("id"),
                            rs.getString("producer_team"),
                            rs.getString("consumer_team")
                    ));
                }
                return list;
            }
        });
    }

    private String rebuildUrlForCatalogSchema(String baseUrl, String catalog, String schema) {
        // naive replacement for .../<catalog>/<schema>?...
        String prefix = "jdbc:trino://";
        int idx = baseUrl.indexOf('/', baseUrl.indexOf(prefix) + prefix.length());
        if (idx == -1) return baseUrl;
        int q = baseUrl.indexOf('?', idx + 1);
        if (q == -1) q = baseUrl.length();
        String pre = baseUrl.substring(0, idx + 1);
        String post = baseUrl.substring(q);
        return pre + catalog + "/" + schema + post;
    }

    private <T> T withConnection(String url, SqlCallable<T> callable) {
        var tr = config.trino();
        Properties props = new Properties();
        if (tr.useKerberos()) {
            props.setProperty("KerberosUseCanonicalHostname", "false");
            props.setProperty("KerberosRemoteServiceName", "trino");
            // Truststore if set
            if (tr.truststorePath() != null && !tr.truststorePath().isBlank()) {
                System.setProperty("javax.net.ssl.trustStore", tr.truststorePath());
                if (tr.truststorePassword() != null) {
                    System.setProperty("javax.net.ssl.trustStorePassword", tr.truststorePassword());
                }
            }
            return kerberos.doAsTicketCache(() -> {
                try (Connection c = DriverManager.getConnection(url, props)) {
                    return callable.call(c);
                }
            });
        } else {
            try (Connection c = DriverManager.getConnection(url, props)) {
                return callable.call(c);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
    }

    @FunctionalInterface
    interface SqlCallable<T> { T call(Connection c) throws Exception; }
}
