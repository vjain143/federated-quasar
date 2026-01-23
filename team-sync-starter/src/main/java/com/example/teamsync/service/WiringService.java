package com.example.teamsync.service;

import com.example.teamsync.model.TrinoRow;
import com.example.teamsync.util.ConfigService;

import java.util.List;
import java.util.Map;

public class WiringService {

    private final TrinoService trino;
    private final MySqlService mysql;
    private final ConfigService.AppConfig config;

    public WiringService(TrinoService trino, MySqlService mysql, ConfigService.AppConfig config) {
        this.trino = trino;
        this.mysql = mysql;
        this.config = config;
    }

    public String runJob(String catalog, String schema, String table, int limit) {
        List<TrinoRow> rows = trino.readRows(catalog, schema, table, limit);
        int fetched = 0;
        int inserted = 0;

        for (TrinoRow r : rows) {
            if (r.producerTeam() == null || r.consumerTeam() == null) continue;

            var producerTeam = findTeam(r.producerTeam());
            var consumerTeam = findTeam(r.consumerTeam());

            Map<String,Object> row = mysql.fetchProducerRow(
                    producerTeam.name(),
                    producerTeam.tables().producerTable(),
                    "id",
                    r.id()
            );
            if (!row.isEmpty()) {
                row = transformRow(row, producerTeam, consumerTeam);
                int n = mysql.insertIntoConsumer(
                        consumerTeam.name(),
                        consumerTeam.tables().consumerTable(),
                        row
                );
                inserted += n;
                fetched += 1;
            }
        }
        return "Job finished: trinoRows=" + rows.size() + ", producerFetched=" + fetched + ", consumerInserted=" + inserted;
    }

    private ConfigService.TeamConfig findTeam(String name) {
        return config.teams().stream().filter(t -> t.name().equalsIgnoreCase(name)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown team: " + name));
    }

    // hook to adjust fields/rename/etc.
    private Map<String,Object> transformRow(Map<String,Object> row, ConfigService.TeamConfig producer, ConfigService.TeamConfig consumer) {
        // no-op by default
        return row;
    }
}
