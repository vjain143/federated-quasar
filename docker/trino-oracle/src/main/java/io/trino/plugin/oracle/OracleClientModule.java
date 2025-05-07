/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package io.trino.plugin.oracle;

import com.google.common.base.Throwables;
import com.google.inject.Binder;
import com.google.inject.Key;
import com.google.inject.Module;
import com.google.inject.Provides;
import com.google.inject.Scopes;
import com.google.inject.Singleton;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.instrumentation.jdbc.datasource.OpenTelemetryDataSource;
import io.trino.plugin.jdbc.BaseJdbcConfig;
import io.trino.plugin.jdbc.ConnectionFactory;
import io.trino.plugin.jdbc.ForBaseJdbc;
import io.trino.plugin.jdbc.JdbcClient;
import io.trino.plugin.jdbc.MaxDomainCompactionThreshold;
import io.trino.plugin.jdbc.RetryStrategy;
import io.trino.plugin.jdbc.TimestampTimeZoneDomain;
import io.trino.plugin.jdbc.credential.CredentialProvider;
import io.trino.plugin.jdbc.ptf.Query;
import io.trino.spi.connector.ConnectorSession;
import io.trino.spi.function.table.ConnectorTableFunction;
import oracle.jdbc.OracleConnection;
import oracle.jdbc.datasource.impl.OracleDataSource;
import org.ietf.jgss.GSSCredential;
import org.ietf.jgss.GSSManager;
import org.ietf.jgss.Oid;

import javax.security.auth.Subject;
import javax.security.auth.login.Configuration;
import javax.security.auth.login.LoginContext;
import java.security.PrivilegedExceptionAction;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.SQLRecoverableException;
import java.util.Optional;
import java.util.Properties;

import static com.google.inject.multibindings.Multibinder.newSetBinder;
import static com.google.inject.multibindings.OptionalBinder.newOptionalBinder;
import static io.airlift.configuration.ConfigBinder.configBinder;
import static io.trino.plugin.jdbc.JdbcModule.bindSessionPropertiesProvider;
import static io.trino.plugin.oracle.OracleClient.ORACLE_MAX_LIST_EXPRESSIONS;

public class OracleClientModule implements Module {
    @Override
    public void configure(Binder binder) {
        binder.bind(JdbcClient.class).annotatedWith(ForBaseJdbc.class).to(OracleClient.class).in(Scopes.SINGLETON);
        newOptionalBinder(binder, TimestampTimeZoneDomain.class).setBinding().toInstance(TimestampTimeZoneDomain.ANY);
        bindSessionPropertiesProvider(binder, OracleSessionProperties.class);
        configBinder(binder).bindConfig(OracleConfig.class);
        newOptionalBinder(binder, Key.get(int.class, MaxDomainCompactionThreshold.class)).setBinding().toInstance(ORACLE_MAX_LIST_EXPRESSIONS);
        newSetBinder(binder, ConnectorTableFunction.class).addBinding().toProvider(Query.class).in(Scopes.SINGLETON);
        newSetBinder(binder, RetryStrategy.class).addBinding().to(OracleRetryStrategy.class).in(Scopes.SINGLETON);
    }

    @Provides
    @Singleton
    @ForBaseJdbc
    public static ConnectionFactory connectionFactory(BaseJdbcConfig config, CredentialProvider credentialProvider, OracleConfig oracleConfig, OpenTelemetry openTelemetry)
            throws SQLException {
        Properties connectionProperties = new Properties();
        connectionProperties.setProperty(OracleConnection.CONNECTION_PROPERTY_INCLUDE_SYNONYMS, String.valueOf(oracleConfig.isSynonymsEnabled()));
        connectionProperties.setProperty(OracleConnection.CONNECTION_PROPERTY_REPORT_REMARKS, String.valueOf(oracleConfig.isRemarksReportingEnabled()));

        try {
            LoginContext loginContext = new LoginContext(
                    "OracleKerberosLoginModule",
                    null,
                    null,
                    Configuration.getInstance("JavaLoginConfig", new javax.security.auth.login.Configuration.Parameters() {
                        @Override
                        public java.net.URI getURI() {
                            return new java.io.File("/path/to/jaas.conf").toURI();
                        }
                    })
            );
            loginContext.login();
            Subject subject = loginContext.getSubject();

            GSSCredential gssCredential = Subject.doAs(subject, (PrivilegedExceptionAction<GSSCredential>) () -> {
                GSSManager manager = GSSManager.getInstance();
                return manager.createCredential(null,
                        GSSCredential.DEFAULT_LIFETIME,
                        (Oid) null,
                        GSSCredential.INITIATE_ONLY);
            });

            OracleDataSource oracleDs = new OracleDataSource();
            oracleDs.setURL(config.getConnectionUrl());
            oracleDs.setConnectionProperties(connectionProperties);

            credentialProvider.getConnectionUser().ifPresent(user -> {
                try {
                    oracleDs.setUser(user);
                } catch (SQLException e) {
                    throw new RuntimeException(e);
                }
            });

            credentialProvider.getConnectionPassword().ifPresent(password -> {
                try {
                    oracleDs.setPassword(password);
                } catch (SQLException e) {
                    throw new RuntimeException(e);
                }
            });

            if (oracleConfig.isConnectionPoolEnabled()) {
                return session -> {
                    return new OpenTelemetryDataSource(new GssCredentialDataSource(oracleDs, gssCredential), openTelemetry)
                            .getConnection();
                };
            } else {
                return session -> {
                    OracleConnection conn = oracleDs.createConnectionBuilder()
                            .gssCredential(gssCredential)
                            .build();
                    conn.setAutoCommit(true);
                    return new OpenTelemetryDataSource(() -> conn, openTelemetry).getConnection();
                };
            }
        }
        catch (Exception e) {
            throw new RuntimeException("Kerberos-enabled Oracle connection failed", e);
        }
    }

    private static class OracleRetryStrategy implements RetryStrategy {
        @Override
        public boolean isExceptionRecoverable(Throwable exception) {
            return Throwables.getCausalChain(exception).stream()
                    .anyMatch(SQLRecoverableException.class::isInstance);
        }
    }
}
