package com.fq.udf;

import io.trino.spi.function.*;
import io.trino.spi.type.StandardTypes;
import io.airlift.slice.Slice;

import java.net.URI;

import static io.airlift.slice.Slices.utf8Slice;

@ScalarFunction("redact_url")
@Description("Redacts sensitive segments in a URL")
public final class RedactFunctions {

    private RedactFunctions() {}

    @SqlType(StandardTypes.VARCHAR)
    public static Slice redactUrl(@SqlType(StandardTypes.VARCHAR) Slice input) {
        String url = input.toStringUtf8();
        try {
            URI uri = new URI(url);
            String[] parts = uri.getPath().split("/");
            if (parts.length > 2) {
                parts[parts.length - 1] = "REDACTED";
            }
            String redactedPath = String.join("/", parts);
            return utf8Slice(new URI(
                    uri.getScheme(),
                    uri.getAuthority(),
                    redactedPath,
                    uri.getQuery(),
                    uri.getFragment()
            ).toString());
        } catch (Exception e) {
            return utf8Slice("INVALID_URL");
        }
    }
}