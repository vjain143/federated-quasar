FROM node:20-bookworm-slim AS ui-builder

WORKDIR /build/ui

COPY moat/ui/package.json moat/ui/package-lock.json ./
RUN npm ci

COPY moat/ui/ ./
RUN npm run build


FROM python:3.12-slim-bookworm AS python-builder

ENV VENV_PATH=/opt/venv
ENV PATH="${VENV_PATH}/bin:${PATH}"

WORKDIR /build

COPY requirements.txt ./

RUN python -m venv "${VENV_PATH}" \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


FROM debian:bookworm-slim AS opa-downloader

ARG TARGETARCH
ARG OPA_VERSION=1.7.1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN case "${TARGETARCH}" in \
        amd64) OPA_ARCH="amd64" ;; \
        arm64) OPA_ARCH="arm64" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" && exit 1 ;; \
    esac \
    && curl -fsSL -o /opa "https://github.com/open-policy-agent/opa/releases/download/v${OPA_VERSION}/opa_linux_${OPA_ARCH}_static" \
    && chmod 755 /opa


FROM python:3.12-slim-bookworm

ARG OPA_VERSION=1.7.1

ENV CONFIG_FILE_PATH=/app/moat/config/config.yaml
ENV PYTHONPATH=/app/moat/src
ENV FLASK_APP=moat.src.app
ENV OPA_VERSION=${OPA_VERSION}
ENV VENV_PATH=/opt/venv
ENV PATH="${VENV_PATH}/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -s /bin/bash -m appuser

RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/moat
WORKDIR /app/moat

COPY --from=python-builder /opt/venv /opt/venv
COPY --from=opa-downloader /opa /usr/local/bin/opa

COPY moat/ /app/moat/
COPY --from=ui-builder /build/ui/static /app/moat/ui/static
COPY opa/ /app/opa
COPY entrypoint.sh /app/
COPY version.txt /app/moat/

RUN chmod +x /app/entrypoint.sh \
    && chown -R appuser:appuser /app /opt/venv

EXPOSE 8000

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["start-server"]
