# FROM python:3.8-slim as base

# Any python libraries that require system libraries to be installed will likely
# need the following packages in order to build
# RUN apt-get update && \
#     apt-get -y upgrade && \
#     apt-get install -y build-essential git && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# FROM base as builder

# WORKDIR /app

# COPY . /app

# RUN pip install -e .[dev,server]

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV APPNAME=stac-fastapi
ENV VERSION=2.4.5

WORKDIR /var/venv

# Ensure this will work within the NRCan network
# RUN update-ca-trust force-enable
# COPY NRCAN-Root-2019-B64.cer /etc/pki/ca-trust/source/anchors/
# RUN update-ca-trust extract


RUN apt-get update
RUN apt-get install -y python3 python3-pip python3.10-venv


# create venv
RUN python3 -m venv /var/venv/$APPNAME
ENV PATH="/var/venv/$APPNAME/bin:$PATH"
RUN pip3 install --upgrade pip


# install all dependencies
COPY requirements.txt /var/venv/$APPNAME-requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r /var/venv/$APPNAME-requirements.txt


# perform cleanup
RUN py3clean /var/venv/$APPNAME
RUN pip uninstall -y pip


# copy updated files from host to venv
COPY stac_fastapi/sqlalchemy/serializers.py /var/venv/$APPNAME/lib/python3.10/site-packages/stac_fastapi/sqlalchemy/serializers.py
COPY alembic/versions/6a37bc5b3b65_change_collection_description_column_.py /var/venv/$APPNAME/lib/python3.10/site-packages/alembic/versions/6a37bc5b3b65_change_collection_description_column_.py

# create tar ball
RUN tar -pczf $APPNAME-2.4.5-venv.tar.gz /var/venv/$APPNAME/


#### run in terminal
# docker build -t stac-fastapi .
# docker create --name stac-fastapi stac-fastapi
# docker cp stac-fastapi:/var/venv/stac-fastapi-2.4.5-venv.tar.gz .
# aws s3 cp stac-fastapi-2.4.5-venv.tar.gz s3://fgp-datacube-$ENV-templates/datacube-apps/server-geo/stac-api/   