package com.example.teamsync.service;

import com.example.teamsync.util.ConfigService;

import java.sql.*;
import java.util.*;
import java.util.stream.Collectors;

public class MySqlService {
    private final ConfigService.AppConfig config;
    private final KerberosAuth kerberos;

    public MySqlService(ConfigService.AppConfig config, KerberosAuth kerberos) {
        this.config = config;
        this.kerberos = kerberos;
    }

    public Map<String,Object> fetchProducerRow(String teamName, String table, String idColumn, Object idValue) {
        var team = findTeam(teamName);
        String sql = "SELECT * FROM " + table + " WHERE " + idColumn + " = ?";
        return withTeamConnection(team, conn -> {
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setObject(1, idValue);
                try (ResultSet rs = ps.executeQuery()) {
                    if (!rs.next()) return Map.of();
                    ResultSetMetaData md = rs.getMetaData();
                    Map<String,Object> row = new LinkedHashMap<>();
                    for (int i=1;i<=md.getColumnCount();i++) {
                        row.put(md.getColumnName(i), rs.getObject(i));
                    }
                    return row;
                }
            }
        });
    }

    public int insertIntoConsumer(String teamName, String table, Map<String,Object> row) {
        var team = findTeam(teamName);
        if (row.isEmpty()) return 0;
        var cols = row.keySet().stream().collect(Collectors.toList());
        String placeholders = String.join(", ", Collections.nCopies(cols.size(), "?"));
        String columnList = String.join(", ", cols);
        String sql = "INSERT INTO " + table + " (" + columnList + ") VALUES (" + placeholders + ")";
        return withTeamConnection(team, conn -> {
            try (PreparedStatement ps = conn.prepareStatement(sql)) {
                int idx = 1;
                for (String col : cols) {
                    ps.setObject(idx++, row.get(col));
                }
                return ps.executeUpdate();
            }
        });
    }

    private ConfigService.TeamConfig findTeam(String name) {
        return config.teams().stream()
                .filter(t -> t.name().equalsIgnoreCase(name))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown team: " + name));
    }

    private <T> T withTeamConnection(ConfigService.TeamConfig team, SqlCallable<T> callable) {
        var m = team.mysql();
        Properties props = new Properties();
        try {
            if ("PASSWORD".equalsIgnoreCase(m.mode())) {
                if ("mysql".equalsIgnoreCase(m.driver())) {
                    Class.forName("com.mysql.cj.jdbc.Driver");
                } else {
                    Class.forName("org.mariadb.jdbc.Driver");
                }
                props.setProperty("user", m.user());
                props.setProperty("password", m.password());
                if (m.extras() != null) m.extras().forEach(props::setProperty);
                try (Connection c = DriverManager.getConnection(m.url(), props)) {
                    return callable.call(c);
                }
            } else if ("KERBEROS_GSSAPI".equalsIgnoreCase(m.mode())) {
                // Requires a Kerberos-capable server/driver (e.g., MariaDB with GSSAPI auth plugin)
                if ("mariadb".equalsIgnoreCase(m.driver())) {
                    Class.forName("org.mariadb.jdbc.Driver");
                } else {
                    Class.forName("com.mysql.cj.jdbc.Driver"); // unlikely to work with Kerberos
                }
                if (m.gssService() != null && !m.gssService().isBlank()) {
                    props.setProperty("gssapiServiceName", m.gssService());
                }
                if (m.extras() != null) m.extras().forEach(props::setProperty);
                return kerberos.doAsTicketCache(() -> {
                    try (Connection c = DriverManager.getConnection(m.url(), props)) {
                        return callable.call(c);
                    }
                });
            } else {
                throw new IllegalArgumentException("Unsupported MySQL auth mode: " + m.mode());
            }
        } catch (Exception e) {
            throw new RuntimeException("MySQL connection failed for team " + team.name() + ": " + e.getMessage(), e);
        }
    }

    @FunctionalInterface
    interface SqlCallable<T> { T call(Connection c) throws Exception; }
}
