# Use Alpine Linux as the base image
FROM arm64v8/alpine:latest

# Install required packages
RUN apk --update add \
    python3 \
    py3-pip \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cyrus-sasl-dev \
    libpq \
    mariadb-connector-c-dev \
    postgresql-dev

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install -y nodejs
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -; \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list; \
    apt-get update; \
    apt-get install -y yarn

# Install Superset
RUN pip3 install --no-cache-dir superset

# Initialize Superset database and create an admin user
RUN superset db upgrade && \
    superset init

# Expose the Superset port
EXPOSE 8088

# Command to run Superset
CMD ["gunicorn", "-b", "0.0.0.0:8088", "superset:app"]
