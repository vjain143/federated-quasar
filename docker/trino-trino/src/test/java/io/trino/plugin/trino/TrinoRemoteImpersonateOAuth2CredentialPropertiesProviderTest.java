package io.trino.plugin.trino;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class TrinoRemoteImpersonateOAuth2CredentialPropertiesProviderTest {

    private TrinoRemoteImpersonateOAuth2CredentialPropertiesProvider instance;

    @BeforeEach
    public void setUp() {
        // Instantiate with default constructor if available
        instance = new TrinoRemoteImpersonateOAuth2CredentialPropertiesProvider();
    }
}
