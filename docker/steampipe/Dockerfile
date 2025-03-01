FROM openjdk:11-slim
LABEL maintainer="Vivek Jain"
LABEL steampipe="0.22.0"
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY --from=docker.io/turbot/steampipe:0.22.0 --chown=999:999 /usr/local/bin/steampipe /usr/local/bin/docker-entrypoint.sh /usr/local/bin/
COPY --from=docker.io/turbot/steampipe:0.22.0 --chown=999:999 /home/steampipe/.steampipe /home/steampipe/.steampipe

RUN apt-get update && \
    apt-get install -y --no-install-recommends tar gzip unzip less krb5-user && \
    rm -rf /var/lib/apt/lists/*

#KLOGIN BINARY SETUP
#RUN cd /usr/local/bin  \
#    && curl -0 /kubecommunity/klogin/0.6.9/klogin-0.6.9-linux-amd64.tar.gz \
#    && tar -xvzf klogin-0.6.9-linux-amd64. tar.gz \
#    && chmod a+x klogin  \
#    && rm -rf klogin-0.6.9-linux-amd64. tar.gz

RUN \
    chmod 777 /usr/local/bin/docker-entrypoint.sh  \
    && sed 's/steampipe:0/fquser:999/g' /usr/local/bin/docker-entrypoint.sh > /usr/local/bin/steampipe-entrypoint.sh \
    && sed -i 's/\/home\/steampipe/\/home\/fquser/g' /usr/local/bin/steampipe-entrypoint.sh \
    && cat /usr/local/bin/steampipe-entrypoint.sh \
    && chmod a+x /usr/local/bin/steampipe-entrypoint.sh \
    && chown -R 999:999 /home/fquser/.steampipe \
    && 1s -al ~fquser/.steampipe

USER fquser

#ENV https_proxy=http://myproxy.net:10443

RUN steampipe plugin install steampipe

RUN steampipe plugin install aws azure azuread kubernetes whois trivy bitbucket cs imap jira ldap net virustotal shodan splunk steampipe plugin update --all  \

# expose postgres service default port
EXPOSE 9193
# expose dashboard service default port
EXPOSE 9194

ENTRYPOINT ["/usr/local/bin/steampipe-entrypoint.sh"]

CMD ["steampipe", "service", "start", "--foreground", "--database-listen=local"]