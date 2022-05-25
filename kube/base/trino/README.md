

#  Download and setup 'trino-cli-380-executable.jar'
```text
curl -O https://repo1.maven.org/maven2/io/trino/trino-cli/380/trino-cli-380-executable.jar
chmod +x trino-cli-380-executable.jar
mv trino-cli-380-executable.jar trino

./trino --server https://localhost:30080/ --user=trino --password
```

# SHOW SESSION

steampipe.properties:
connector.name=postgresql
connection-url=jdbc:postgresql://localhost:9193/steampipe
connection-user=steampipe
connection-password=steampipe123

#Steampipe Plugins
- mountPath: etc/trino/catalog/steampipe.properties
  name: trino-configmap-volume
  subPath: steampipe.properties



hive-metastore.properties:
connector.name=hive-hadoop2
hive.metastore.uri=thrift://metastore:9083
hive.metastore-timeout=130s
hive.create-empty-bucket-files=true
hive.allow-drop-table=true
hive.max-partitions-per-scan=1000000
hive.s3.endpoint=http://minio:9000
hive.s3.path-style-access=true
hive.s3.ssl.enabled=false
hive.s3.max-connections=100
hive.s3.aws-access-key=minio
hive.s3.aws-secret-key=minio123
hive.non-managed-table-writes-enabled=true
iceberg.properties:
connector.name=iceberg
hive.metastore.uri=thrift://metastore:9083
hive.metastore-timeout=130s
hive.create-empty-bucket-files=true
hive.allow-drop-table=true
hive.max-partitions-per-scan=1000000
hive.s3.endpoint=http://minio:9000
hive.s3.path-style-access=true
hive.s3.ssl.enabled=false
hive.s3.max-connections=100
hive.s3.aws-access-key=minio
hive.s3.aws-secret-key=minio123
hive.non-managed-table-writes-enabled=true
mysql.properties:
connector.name=mysql
connection-url=jdbc:mysql://mysql:13306/?useSSL=false
connection-user=root
connection-password=my_password


- mountPath: etc/trino/catalog/iceberg.properties
  name: trino-configmap-volume
  subPath: iceberg.properties
- mountPath: etc/trino/catalog/mysql.properties
  name: trino-configmap-volume
  subPath: mysql.properties
#Steampipe Plugins
- mountPath: etc/trino/catalog/steampipe.properties
  name: trino-configmap-volume
  subPath: steampipe.properties