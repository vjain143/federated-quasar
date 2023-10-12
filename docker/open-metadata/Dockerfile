FROM centos:latest

# Copy the script into the image
COPY install_jdk.sh /usr/local/bin/

# Make the script executable
#RUN chmod +x /usr/local/bin/install_jdk.sh

ENV JDK_VERSION=8u291
ENV JDK_URL="https://download.oracle.com/otn/java/jdk/8u291-b10/aa0333dd3019491ca4f6ddbe78cdb6d0/jdk-${JDK_VERSION}-linux-x64.tar.gz"

# Download JDK
RUN curl -L -b "oraclelicense=accept-securebackup-cookie" -o /tmp/jdk.tar.gz ${JDK_URL}
RUN tar -xzf /tmp/jdk.tar.gz -C /usr/local/jdk

# Run the script
RUN /usr/local/bin/install_jdk.sh
#FROM openjdk:17-slim

#RUN apt-get update && \
#    apt-get install -y curl --no-install-recommends && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/local/jdk
ENV PATH=$PATH:$JAVA_HOME/bin

RUN mkdir /opt/open-metadata
RUN chmod -R 775 /opt/open-metadata

RUN cd /opt/open-metadata \
    && curl -L https://github.com/open-metadata/OpenMetadata/releases/download/1.1.7-release/openmetadata-1.1.7.tar.gz | tar \
    --strip 1 -xzf - -C /opt/open-metadata

RUN chmod 777 /opt/open-metadata/bin/openmetadata-server-start.sh
RUN chmod 777 /opt/open-metadata/bin/openmetadata.sh

EXPOSE 8585

CMD ["./opt/open-metadata/bin/openmetadata-server-start.sh"]