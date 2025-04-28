package com.fq.udf;

import com.google.common.collect.ImmutableSet;
import io.trino.spi.Plugin;

import java.util.Set;

public class RedactUdfPlugin implements Plugin {

    @Override
    public Set<Class<?>> getFunctions() {
        return ImmutableSet.of(RedactFunctions.class);
    }
}