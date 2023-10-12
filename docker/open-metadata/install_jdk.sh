#!/bin/bash

# Define JDK version
JDK_VERSION=8u291

# Define download URL
JDK_URL="https://download.oracle.com/otn/java/jdk/8u291-b10/aa0333dd3019491ca4f6ddbe78cdb6d0/jdk-${JDK_VERSION}-linux-x64.tar.gz"

# Download JDK
curl -L -b "oraclelicense=accept-securebackup-cookie" -o /tmp/jdk.tar.gz ${JDK_URL}

# Extract JDK
tar -xzf /tmp/jdk.tar.gz -C /usr/local/jdk

# Set environment variables
export JAVA_HOME=/usr/local/jdk${JDK_VERSION}
export PATH=$JAVA_HOME/bin:$PATH

# Clean up
rm /tmp/jdk.tar.gz
