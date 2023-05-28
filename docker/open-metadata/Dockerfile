FROM openjdk:17-slim



RUN apt-get update && \
    apt-get install -y curl --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/open-metadata
RUN chmod -R 775 /opt/open-metadata

COPY openmetadata-*.tar.gz /
RUN tar zxvf openmetadata-*.tar.gz && \
    rm openmetadata-*.tar.gz


COPY openmetadata-start.sh ./
COPY bootstrap/* ./
COPY conf/* ./

RUN chmod 777 /openmetadata-start.sh

EXPOSE 8585

CMD ["./openmetadata-start.sh"]