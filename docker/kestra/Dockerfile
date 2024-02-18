# Use a base image with Java support
FROM openjdk:11-jre-slim

# Set the working directory
WORKDIR /app

RUN curl -O https://repo1.maven.org/maven2/io/kestra/kestra/0.13.1/kestra-0.13.1.zip \
    && unzip kestra-0.13.1.zip  \
    && rm kestra-0.13.1.zip

# Define the entry point for your application
CMD ["./kestra/bin/kestra", "start"]
