# Custom Postgres image with PostGIS and pgvector for the playbook stack.
#
# The playbook requires both extensions in one database so evidence, findings,
# and spatial comps can be joined in SQL. The pgvector base image supplies
# pgvector; the Debian PostGIS packages add geometry/geography support.

FROM pgvector/pgvector:pg16

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-16-postgis-3 \
        postgresql-16-postgis-3-scripts \
    && rm -rf /var/lib/apt/lists/*

# Keep the official entrypoint's default root user: it fixes volume ownership
# and then drops to the postgres user before starting the server.
