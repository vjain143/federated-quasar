package com.example.teamsync.api;

import com.example.teamsync.model.TrinoRow;
import com.example.teamsync.service.TrinoService;
import io.javalin.Javalin;

import java.util.List;

public class TrinoApi {
    private final TrinoService trino;

    public TrinoApi(Javalin app, TrinoService trino) {
        this.trino = trino;
        app.get("/api/trino/rows", ctx -> {
            String catalog = ctx.queryParam("catalog", "hive");
            String schema = ctx.queryParam("schema", "default");
            String table = ctx.queryParam("table", "events");
            int limit = Integer.parseInt(ctx.queryParam("limit", "50"));
            List<TrinoRow> list = trino.readRows(catalog, schema, table, limit);
            ctx.json(list);
        });
    }
}
