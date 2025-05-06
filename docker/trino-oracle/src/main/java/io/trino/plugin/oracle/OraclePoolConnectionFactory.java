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

import io.airlift.units.Duration;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.instrumentation.jdbc.datasource.OpenTelemetryDataSource;
import io.trino.plugin.jdbc.ConnectionFactory;
import io.trino.plugin.jdbc.credential.CredentialProvider;
import io.trino.spi.connector.ConnectorSession;
import oracle.jdbc.pool.OracleDataSource;
import oracle.ucp.jdbc.PoolDataSource;
import oracle.ucp.jdbc.PoolDataSourceFactory;
import org.ietf.jgss.GSSCredential;
import org.ietf.jgss.GSSManager;
import org.ietf.jgss.Oid;

import javax.security.auth.Subject;
import javax.sql.DataSource;
import java.security.PrivilegedActionException;
import java.security.PrivilegedExceptionAction;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.Optional;
import java.util.Properties;

import static java.lang.Math.toIntExact;
import static java.util.concurrent.TimeUnit.SECONDS;

public class OraclePoolConnectionFactory
        implements ConnectionFactory
{
    private final OpenTelemetryDataSource dataSource;

    public OraclePoolConnectionFactory(
            String connectionUrl,
            Properties connectionProperties,
            CredentialProvider credentialProvider,
            int connectionPoolMinSize,
            int connectionPoolMaxSize,
            Duration inactiveConnectionTimeout,
            OpenTelemetry openTelemetry)
            throws SQLException, PrivilegedActionException {

        // Set up the connection properties
        // Set up the JAAS configuration for Kerberos authentication
        // Initialize the JAAS login context
        OracleKerberosUtils oracleKerberosUtils = new OracleKerberosUtils();
        Subject subject = oracleKerberosUtils.loginWithJaas("OracleKerberosLoginModule", "/path/to/jaas.conf");

        // Create a GSSCredential using the subject
        GSSCredential gssCredential = Subject.doAs(subject, (PrivilegedExceptionAction<GSSCredential>) () -> {
            GSSManager manager = GSSManager.getInstance();
            return manager.createCredential(null,
                    GSSCredential.DEFAULT_LIFETIME,
                    (Oid) null,
                    GSSCredential.INITIATE_ONLY);
        });

        // Create the Oracle UCP data source
        PoolDataSource dataSource = PoolDataSourceFactory.getPoolDataSource();

        //Setting connection properties of the data source
        dataSource.setConnectionFactoryClassName(OracleDataSource.class.getName());


        //Setting pool properties
        dataSource.setInitialPoolSize(connectionPoolMinSize);
        dataSource.setMinPoolSize(connectionPoolMinSize);
        dataSource.setMaxPoolSize(connectionPoolMaxSize);
        dataSource.setValidateConnectionOnBorrow(true);
        dataSource.setInactiveConnectionTimeout(toIntExact(inactiveConnectionTimeout.roundTo(SECONDS)));

        //Setting connection properties
        credentialProvider.getConnectionUser(Optional.empty())
                .ifPresent(user -> {
                    try {
                        dataSource.setUser(user);
                    }
                    catch (SQLException e) {
                        throw new RuntimeException(e);
                    }
                });
        /*
        credentialProvider.getConnectionPassword(Optional.empty())
                .ifPresent(password -> {
                    try {
                        dataSource.setPassword(password);
                    }
                    catch (SQLException e) {
                        throw new RuntimeException(e);
                    }
                });
        */
        //Setting connection properties
        OracleDataSource oracleDs = new OracleDataSource();
        dataSource.setURL(connectionUrl);
        oracleDs.setConnectionProperties(connectionProperties); // Optional
        // Set the connection properties for the OracleDataSource
        DataSource gssDs = new GssCredentialDataSource(oracleDs, gssCredential);
        this.dataSource = new OpenTelemetryDataSource(gssDs, openTelemetry);
    }

    @Override
    public Connection openConnection(ConnectorSession session)
            throws SQLException
    {
        Connection connection = dataSource.getConnection();
        // Oracle's pool doesn't reset autocommit state of connections when reusing them so we explicitly enable
        // autocommit by default to match the JDBC specification.
        connection.setAutoCommit(true);
        return connection;
    }
}
