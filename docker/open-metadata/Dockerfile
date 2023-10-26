FROM openjdk:17-slim

RUN apt-get update && \
    apt-get install -y curl --no-install-recommends && \
    apt-get install -y procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/open-metadata
RUN chmod -R 775 /opt/open-metadata

RUN cd /opt/open-metadata \
    && curl -L https://github.com/open-metadata/OpenMetadata/releases/download/1.1.7-release/openmetadata-1.1.7.tar.gz | tar \
    --strip 1 -xzf - -C /opt/open-metadata

RUN chmod 777 /opt/open-metadata/bin/openmetadata-server-start.sh
RUN chmod 777 /opt/open-metadata/bin/openmetadata.sh

ENV JAVA_HOME=/usr/local/openjdk-17
ENV PATH=$PATH:$JAVA_HOME/bin

EXPOSE 8585

CMD ["./opt/open-metadata/bin/openmetadata-server-start.sh"]