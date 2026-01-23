package com.example.teamsync.service;

import com.example.teamsync.util.ConfigService;
import javax.security.auth.Subject;
import javax.security.auth.login.LoginContext;
import java.security.PrivilegedAction;
import java.util.concurrent.Callable;

public class KerberosAuth {
    private final ConfigService.AppConfig config;

    public KerberosAuth(ConfigService.AppConfig config) {
        this.config = config;
    }

    public <T> T doAsTicketCache(Callable<T> callable) {
        try {
            LoginContext lc = new LoginContext("Client");
            lc.login();
            Subject subject = lc.getSubject();
            return Subject.doAs(subject, (PrivilegedAction<T>) () -> {
                try { return callable.call(); } catch (Exception e) { throw new RuntimeException(e); }
            });
        } catch (Exception e) {
            throw new RuntimeException("Kerberos login via ticket cache failed: " + e.getMessage(), e);
        }
    }
}
