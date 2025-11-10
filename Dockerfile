FROM python:3.11-slim-bookworm

WORKDIR /app

ARG UID=10001
ARG GID=10001

RUN groupadd --gid ${GID} app \
    && useradd --uid ${UID} --gid ${GID} --home-dir /home/app --create-home app

RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    gcc \
    git \
    tree \
    libpq-dev \
    gdal-bin libgdal-dev \
    libproj-dev libgeos-dev binutils \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER ${UID}:${GID}

RUN pip install --upgrade pip 

COPY --chown=${UID}:${GID} requirements.txt .

RUN  pip install --no-cache-dir -r requirements.txt

COPY --chown=${UID}:${GID} . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
