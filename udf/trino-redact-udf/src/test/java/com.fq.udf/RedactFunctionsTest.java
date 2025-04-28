package com.fq.udf;

import io.airlift.slice.Slice;
import org.testng.annotations.Test;

import static io.airlift.slice.Slices.utf8Slice;
import static org.junit.Assert.*;

public class RedactFunctionsTest {


    // Valid URL with path segments has last segment redacted
    @Test
    public void test_redact_url_with_path_segments() {
        String url = "https://example.com/api/users/12345";
        Slice input = utf8Slice(url);
    
        Slice result = RedactFunctions.redactUrl(input);
    
        String expected = "https://example.com/api/users/REDACTED";
        assertEquals(expected, result.toStringUtf8());
    }

    // URL with no path segments returns unchanged URL
    @Test
    public void test_redact_url_with_no_path_segments() {
        String url = "https://example.com";
        Slice input = utf8Slice(url);
    
        Slice result = RedactFunctions.redactUrl(input);
    
        assertEquals(url, result.toStringUtf8());
    }
}