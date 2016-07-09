FROM ubuntu:16.10

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y python python-dev python-distribute python-pip git libssl-dev

RUN pip install telepot paramiko

RUN mkdir -p /opt/octopus && \
cd /opt/octopus && \
CACHE=1 git clone https://github.com/GustavoKatel/octopus.git

RUN mkdir -p /opt/octopus/conf

VOLUME /opt/octopus/octopus/conf

COPY entrypoint.sh /opt/octopus/

ENTRYPOINT bash /opt/octopus/entrypoint.sh
