package io.trino.plugin.trino;

import com.google.common.collect.ImmutableSet;
import com.google.inject.Inject;
import io.trino.plugin.jdbc.DefaultJdbcMetadataFactory;
import io.trino.plugin.jdbc.IdentityCacheMapping;
import io.trino.plugin.jdbc.JdbcClient;
import io.trino.plugin.jdbc.JdbcMetadata;
import io.trino.plugin.jdbc.JdbcQueryEventListener;
import io.trino.plugin.jdbc.TimestampTimeZoneDomain;

import java.util.Set;

import static java.util.Objects.requireNonNull;

public class TrinoRemoteMetadataFactory
        extends DefaultJdbcMetadataFactory
{
    private final Set<JdbcQueryEventListener> jdbcQueryEventListeners;
    private final TimestampTimeZoneDomain timestampTimeZoneDomain;

    @Inject
    public TrinoRemoteMetadataFactory(
            JdbcClient jdbcClient,
            TimestampTimeZoneDomain timestampTimeZoneDomain,
            Set<JdbcQueryEventListener> jdbcQueryEventListeners,
            IdentityCacheMapping identityCacheMapping)
    {
        super(jdbcClient, timestampTimeZoneDomain, jdbcQueryEventListeners, identityCacheMapping);
        this.jdbcQueryEventListeners = ImmutableSet.copyOf(requireNonNull(jdbcQueryEventListeners, "jdbcQueryEventListeners is null"));
        this.timestampTimeZoneDomain = requireNonNull(timestampTimeZoneDomain, "timestampTimeZoneDomain is null");
    }

    @Override
    protected JdbcMetadata create(JdbcClient transactionCachingJdbcClient)
    {
        return new TrinoRemoteMetadata(transactionCachingJdbcClient, this.timestampTimeZoneDomain, this.jdbcQueryEventListeners);
    }
}