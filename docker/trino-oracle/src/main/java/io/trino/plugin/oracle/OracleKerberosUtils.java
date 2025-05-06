package io.trino.plugin.oracle;

import javax.security.auth.Subject;
import javax.security.auth.login.Configuration;
import javax.security.auth.login.LoginContext;
import java.io.File;
import java.net.URI;

public final class OracleKerberosUtils {
    OracleKerberosUtils() {}

    public static Subject loginWithJaas(String loginContextName, String jaasFilePath) {
        try {
            Configuration config = Configuration.getInstance(
                    "JavaLoginConfig",
                    new javax.security.auth.login.Configuration.Parameters() {
                        public URI getURI() {
                            try {
                                return new File(jaasFilePath).toURI();
                            } catch (Exception e) {
                                throw new RuntimeException("Invalid JAAS file path", e);
                            }
                        }
                    }
            );

            LoginContext loginContext = new LoginContext(loginContextName, null, null, config);
            loginContext.login();
            return loginContext.getSubject();
        } catch (Exception e) {
            throw new RuntimeException("Kerberos login failed for context: " + loginContextName, e);
        }
    }
}
