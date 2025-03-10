kubectl exec -it service/mysql  -n lab -- bash

# Connect to MySQL server using MySQL CLI
mysql -u root -p

# Replace <username> with your MySQL username and enter the password when prompted

# Now, you're in the MySQL CLI. Create a database (replace <database_name> with your desired database name)
CREATE DATABASE metastore_db;

#
CREATE DATABASE openmetadata;
CREATE USER 'openmetadata'@'%' IDENTIFIED BY 'openmetadata123';
GRANT ALL PRIVILEGES ON openmetadata.* TO 'openmetadata_user'@'%' WITH GRANT OPTION;
commit;
# Exit MySQL CLI

CREATE DATABASE airflow;
CREATE USER 'airflow'@'%' IDENTIFIED BY 'airflow123';
GRANT ALL PRIVILEGES ON airflow.* TO 'airflow'@'%' WITH GRANT OPTION;
commit;

CREATE DATABASE gravitino;
CREATE USER 'gravitino'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON gravitino.* TO 'gravitino'@'%' WITH GRANT OPTION;
commit;


CREATE DATABASE nessie;
CREATE USER 'nessie'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON nessie.* TO 'nessie'@'%' WITH GRANT OPTION;
commit;

CREATE DATABASE openmetadata_db;
CREATE USER 'openmetadata'@'%' IDENTIFIED BY 'openmetadata_password';
GRANT ALL PRIVILEGES ON openmetadata_db.* TO 'openmetadata'@'%';
FLUSH PRIVILEGES;

exit


