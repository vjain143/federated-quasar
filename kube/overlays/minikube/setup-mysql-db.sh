kubectl exec -it <mysql-pod-name> -n <namespace> -- bash

# Connect to MySQL server using MySQL CLI
mysql -u <username> -p

# Replace <username> with your MySQL username and enter the password when prompted

# Now, you're in the MySQL CLI. Create a database (replace <database_name> with your desired database name)
CREATE DATABASE <database_name>;

# Exit MySQL CLI
exit