FROM python:3.13-slim

WORKDIR /app

COPY README.md review-studio ./
COPY src ./src

ENTRYPOINT ["sh", "/app/review-studio"]
CMD ["--help"]
