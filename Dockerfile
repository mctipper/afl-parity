ARG UV_VERSION=0.6.4
ARG DEBIAN_VERSION=bookworm

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

# anything slim
FROM debian:$DEBIAN_VERSION-slim

# uv setup
COPY --from=uv /uv /uvx /bin/

# copy files and take ownership
WORKDIR /afl-parity
COPY pyproject.toml .
COPY uv.lock .
COPY .python-version .
COPY src/ ./src/
COPY output/ ./output/
COPY scripts/ ./scripts/

# env variables
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_NO_CACHE=1
ENV UV_FROZEN=1
ENV UV_PROJECT_ENVIRONMENT=/home/root/.venv
ENV PATH="/home/root/.venv/bin:$PATH"

# install dependencies
RUN uv sync --compile-bytecode --no-dev

# Change permissions of the output directory
RUN chmod -R 777 /afl-parity/output

# run script
CMD ["sh", "scripts/run.sh"]