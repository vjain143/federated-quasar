package com.example.teamsync.api;

import com.example.teamsync.service.EmailService;
import com.example.teamsync.service.MySqlService;
import com.example.teamsync.service.TrinoService;
import com.example.teamsync.service.WiringService;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.javalin.Javalin;

import java.util.Map;

public class JobApi {
    private final WiringService wiring;
    private final EmailService email;
    private final ObjectMapper mapper = new ObjectMapper();

    public JobApi(Javalin app, TrinoService trino, MySqlService mysql, EmailService email) {
        this.wiring = new WiringService(trino, mysql, com.example.teamsync.util.ConfigService.load());
        this.email = email;

        app.post("/api/job/run", ctx -> {
            Map<String,Object> body = mapper.readValue(ctx.body(), Map.class);
            String catalog = (String) body.getOrDefault("catalog", "hive");
            String schema = (String) body.getOrDefault("schema", "default");
            String table = (String) body.getOrDefault("table", "events");
            int limit = ((Number) body.getOrDefault("limit", 50)).intValue();

            String summary = wiring.runJob(catalog, schema, table, limit);
            email.sendIfEnabled("Team Sync Job", summary);
            ctx.result(summary);
        });
    }
}
