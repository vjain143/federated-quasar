package io.trino.plugin.oracle;

import oracle.jdbc.OracleConnection;
import oracle.jdbc.datasource.impl.OracleDataSource;
import org.ietf.jgss.GSSCredential;

import javax.sql.DataSource;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.logging.Logger;

public class GssCredentialDataSource implements DataSource {
    private final OracleDataSource oracleDataSource;
    private final GSSCredential gssCredential;

    public GssCredentialDataSource(OracleDataSource oracleDataSource, GSSCredential gssCredential) {
        this.oracleDataSource = oracleDataSource;
        this.gssCredential = gssCredential;
    }

    @Override
    public Connection getConnection() throws SQLException {
        OracleConnection conn = oracleDataSource.createConnectionBuilder()
                .gssCredential(gssCredential)
                .build();
        conn.setAutoCommit(true);
        return conn;
    }

    @Override
    public Connection getConnection(String username, String password) {
        throw new UnsupportedOperationException("Username/password not supported with GSSCredential");
    }

    @Override
    public PrintWriter getLogWriter() throws SQLException {
        return oracleDataSource.getLogWriter();
    }

    @Override
    public void setLogWriter(PrintWriter out) throws SQLException {
        oracleDataSource.setLogWriter(out);
    }

    @Override
    public void setLoginTimeout(int seconds) throws SQLException {
        oracleDataSource.setLoginTimeout(seconds);
    }

    @Override
    public int getLoginTimeout() throws SQLException {
        return oracleDataSource.getLoginTimeout();
    }

    @Override
    public Logger getParentLogger() {
        return Logger.getLogger("oracle.jdbc");
    }

    @Override
    public <T> T unwrap(Class<T> iface) throws SQLException {
        if (iface.isInstance(this)) {
            return iface.cast(this);
        }
        throw new SQLException("No wrapper for " + iface);
    }

    @Override
    public boolean isWrapperFor(Class<?> iface) {
        return iface.isInstance(this);
    }
}
