package com.example.teamsync.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.File;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public class ConfigService {

    public static AppConfig load() {
        try {
            var yaml = new ObjectMapper(new YAMLFactory());
            var app = yaml.readValue(new File("config/application.yaml"), Map.class);
            var teams = yaml.readValue(new File("config/teams.yaml"), Map.class);
            return AppConfig.from(app, teams);
        } catch (Exception e) {
            throw new RuntimeException("Failed to load config: " + e.getMessage(), e);
        }
    }

    public record AppConfig(
            int serverPort,
            TrinoConfig trino,
            HmsConfig hms,
            EmailConfig email,
            List<TeamConfig> teams
    ) {
        @SuppressWarnings("unchecked")
        public static AppConfig from(Map<String,Object> app, Map<String,Object> teamsYaml) {
            var server = (Map<String,Object>) app.getOrDefault("server", Map.of());
            int port = ((Number) server.getOrDefault("port", 8080)).intValue();

            var trino = TrinoConfig.from((Map<String,Object>) app.get("trino"));
            var hms = HmsConfig.from((Map<String,Object>) app.get("hms"));
            var email = EmailConfig.from((Map<String,Object>) app.get("email"));

            var teamsList = (List<Map<String,Object>>) teamsYaml.get("teams");
            var teamConfigs = teamsList.stream().map(TeamConfig::from).toList();

            return new AppConfig(port, trino, hms, email, teamConfigs);
        }
    }

    public record TrinoConfig(
            String jdbcUrl,
            boolean useKerberos,
            String principal,
            String keytab,
            boolean useTicketCache,
            String truststorePath,
            String truststorePassword
    ) {
        @SuppressWarnings("unchecked")
        public static TrinoConfig from(Map<String,Object> m) {
            if (m == null) m = Map.of();
            return new TrinoConfig(
                    (String)m.getOrDefault("jdbcUrl", ""),
                    (boolean)m.getOrDefault("useKerberos", false),
                    (String)m.getOrDefault("principal", ""),
                    (String)m.getOrDefault("keytab", ""),
                    (boolean)m.getOrDefault("useTicketCache", true),
                    (String)m.getOrDefault("truststorePath", ""),
                    (String)m.getOrDefault("truststorePassword", "")
            );
        }
    }

    public record HmsConfig(
            String uris,
            boolean useKerberos,
            String principal,
            boolean useTicketCache
    ) {
        @SuppressWarnings("unchecked")
        public static HmsConfig from(Map<String,Object> m) {
            if (m == null) m = Map.of();
            return new HmsConfig(
                    (String)m.getOrDefault("uris", "thrift://localhost:9083"),
                    (boolean)m.getOrDefault("useKerberos", false),
                    (String)m.getOrDefault("principal", ""),
                    (boolean)m.getOrDefault("useTicketCache", true)
            );
        }
    }

    public record EmailConfig(
            boolean enabled,
            String smtpHost,
            int smtpPort,
            String username,
            String password,
            String from,
            List<String> to
    ) {
        @SuppressWarnings("unchecked")
        public static EmailConfig from(Map<String,Object> m) {
            if (m == null) m = Map.of();
            return new EmailConfig(
                    (boolean)m.getOrDefault("enabled", false),
                    (String)m.getOrDefault("smtpHost", ""),
                    ((Number)m.getOrDefault("smtpPort", 587)).intValue(),
                    (String)m.getOrDefault("username", ""),
                    (String)m.getOrDefault("password", ""),
                    (String)m.getOrDefault("from", ""),
                    (List<String>)m.getOrDefault("to", List.of())
            );
        }
    }

    public record TeamConfig(
            String name,
            String schema,
            TablePair tables,
            MySql mysql
    ) {
        @SuppressWarnings("unchecked")
        public static TeamConfig from(Map<String,Object> m) {
            var name = (String)m.get("name");
            var schema = (String)m.get("schema");
            var tables = TablePair.from((Map<String,Object>)m.get("tables"));
            var mysql = MySql.from((Map<String,Object>)m.get("mysql"));
            return new TeamConfig(name, schema, tables, mysql);
        }
    }

    public record TablePair(String producerTable, String consumerTable) {
        public static TablePair from(Map<String,Object> m) {
            return new TablePair(
                    (String)m.getOrDefault("producerTable", "items"),
                    (String)m.getOrDefault("consumerTable", "items_ingest")
            );
        }
    }

    public record MySql(
            String driver,       // mysql | mariadb
            String mode,         // PASSWORD | KERBEROS_GSSAPI
            String url,
            String user,
            String password,
            String gssService,
            boolean useTicketCache,
            Map<String,String> extras
    ) {
        @SuppressWarnings("unchecked")
        public static MySql from(Map<String,Object> m) {
            if (m == null) m = Map.of();
            return new MySql(
                    (String)m.getOrDefault("driver", "mysql"),
                    (String)m.getOrDefault("mode", "PASSWORD"),
                    (String)m.getOrDefault("url", ""),
                    (String)m.getOrDefault("user", ""),
                    (String)m.getOrDefault("password", ""),
                    (String)m.getOrDefault("gssService", ""),
                    (boolean)m.getOrDefault("useTicketCache", true),
                    (Map<String,String>)m.getOrDefault("extras", Map.of())
            );
        }
    }
}
