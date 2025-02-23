


-------
FROM openjdk:21-ea-oracle
LABEL maintainer="Vivek Jain"

ENV TRINO_VERSION 443
ENV TRINO_TAR_DISTRIBUTION_URL="https://repo.maven.apache.org/maven2/io/trino/trino-server/${TRINO_VERSION}/trino-server-${TRINO_VERSION}.tar.gz"

RUN microdnf install --nodocs tar gzip less python3 \
&& mkdir -p /usr/lib/trino /data/trino \
&& chown -R "999:999" /usr/lib/trino /data/trino \
&& microdf clean all


RUN set -xeu && \
&& curl $(PRESTO LOCATION) | tar -C /usr/lib/trino -xz --strip 1 \
&& chown -R 999:999 /usr/lib/trino /data/trino \
&& 1s -al /usr/lib/trino \
&& ls -al /data/trino \
&& ls -al /usr/bin/trino

#COPY --chown-999:999 bin/* /usr/lib/trino/bin/
#COPY --chown-999:999 default /usr/lib/trino/default/

RUN chown -R 999:999 /usr/11b/trino /data/trino \
&& 1s -al /usr/lib/trino/bin \
&& ls -al /data/trino \
&& 1s -al /usr/lib/trino \
&& ls -al /usr/lib/trino/default \
&& ls -al /usr/lib/trino/default/etc

ENV LANG en US.UTF-8
EXPOSE 8080
USER jpmenobody
CMD ["/usr/lib/trino/bin/run-trino"]