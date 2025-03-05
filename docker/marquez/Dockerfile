FROM openjdk:11-jre-slim

# Set environment variables
ENV MARQUEZ_VERSION=0.50.0
ENV MARQUEZ_HOME=/opt/marquez
ENV MARQUEZ_DB_USERNAME=marquez
ENV MARQUEZ_DB_PASSWORD=marquez
ENV MARQUEZ_DB_DATABASE=marquez
ENV MARQUEZ_DB_HOST=localhost
ENV MARQUEZ_DB_PORT=5432

# Create working directory
RUN mkdir -p $MARQUEZ_HOME
WORKDIR $MARQUEZ_HOME

# Download and extract Marquez
#https://github.com/MarquezProject/marquez/archive/refs/tags/0.50.0.tar.gz
#RUN wget https://github.com/MarquezProject/marquez/releases/download/$MARQUEZ_VERSION/marquez-$MARQUEZ_VERSION.tar.gz \
RUN wget https://github.com/MarquezProject/marquez/archive/refs/tags/0.50.0.tar.gz \
    && tar -xvzf marquez-0.50.0.tar.gz \
    && rm marquez-0.50.0.tar.gz

# Expose ports
EXPOSE 5000 5432

# Start Marquez
CMD ["/opt/marquez/bin/marquez", "--config", "/opt/marquez/config.yml"]
