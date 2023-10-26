kubectl exec -it <mysql-pod-name> -n <namespace> -- bash

# Connect to MySQL server using MySQL CLI
mysql -u root -p

# Replace <username> with your MySQL username and enter the password when prompted

# Now, you're in the MySQL CLI. Create a database (replace <database_name> with your desired database name)
CREATE DATABASE metastore_db;

CREATE DATABASE openmetadata_db;
CREATE USER 'openmetadata_user'@'%' IDENTIFIED BY 'openmetadata_password';
GRANT ALL PRIVILEGES ON openmetadata_db.* TO 'openmetadata_user'@'%' WITH GRANT OPTION;
commit;


CREATE DATABASE openmetadata;
CREATE USER 'openmetadata'@'%' IDENTIFIED BY 'openmetadata123';
GRANT ALL PRIVILEGES ON openmetadata.* TO 'openmetadata_user'@'%' WITH GRANT OPTION;
commit;
# Exit MySQL CLI
exit


