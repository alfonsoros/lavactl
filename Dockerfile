FROM python:2.7

ARG user
ARG token
ARG master_addr
ARG ftp_user
ARG ftp_pass

ENV LAVA_SERVER_ADDR=$master_addr
ENV LAVA_USER=$user
ENV LAVA_TOKEN=$token
ENV LAVA_STORAGE_FTP_USER=$ftp_user
ENV LAVA_STORAGE_FTP_PASS=$ftp_pass

RUN pip install jinja2 paramiko PyYAML progress artifactory

ADD . /lava-ctl
WORKDIR /lava-ctl

ENTRYPOINT [ "python", "./lava-ctl.py" ]
