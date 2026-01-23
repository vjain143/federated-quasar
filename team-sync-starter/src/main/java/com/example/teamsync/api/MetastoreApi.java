package com.example.teamsync.api;

import com.example.teamsync.service.HiveMetaService;
import io.javalin.Javalin;

public class MetastoreApi {
    public MetastoreApi(Javalin app, HiveMetaService hms) {
        app.get("/api/hms/databases", ctx -> {
            ctx.json(hms.listDatabases());
        });
    }
}
