package com.example.teamsync;

import com.example.teamsync.api.JobApi;
import com.example.teamsync.api.MetastoreApi;
import com.example.teamsync.api.TrinoApi;
import com.example.teamsync.service.*;
import com.example.teamsync.util.ConfigService;
import io.javalin.Javalin;
import io.javalin.http.staticfiles.Location;

public class App {
    public static void main(String[] args) {
        var config = ConfigService.load();
        int port = config.serverPort();

        var kerberos = new KerberosAuth(config);
        var trino = new TrinoService(config, kerberos);
        var mysql = new MySqlService(config, kerberos);
        var hms = new HiveMetaService(config, kerberos);
        var email = new EmailService(config);

        var app = Javalin.create(c -> {
            c.bundledPlugins.enableCors(cors -> cors.addRule(rule -> rule.anyHost()));
            c.staticFiles.add("/static", Location.CLASSPATH);
            c.staticFiles.add("/swagger", Location.CLASSPATH);
        }).start(port);

        // Serve Swagger
        app.get("/swagger", ctx -> ctx.redirect("/swagger/index.html"));
        app.get("/", ctx -> ctx.redirect("/ui"));
        app.get("/ui", ctx -> ctx.redirect("/static/index.html"));
        app.get("/openapi.yaml", ctx -> ctx.result(App.class.getResourceAsStream("/openapi.yaml")));

        new TrinoApi(app, trino);
        new MetastoreApi(app, hms);
        new JobApi(app, trino, mysql, email);
    }
}
