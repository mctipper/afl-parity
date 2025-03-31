ARG UV_VERSION=0.6.4
ARG DEBIAN_VERSION=bookworm

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

FROM mcr.microsoft.com/vscode/devcontainers/base:$DEBIAN_VERSION

COPY --from=uv --chown=vscode: /uv /uvx /bin/

RUN mkdir -p /afl-parity/output && \
    chmod -R 777 /afl-parity/output && \
    chown -R vscode: /afl-parity/output