FROM python:2.7

RUN pip install jinja2 paramiko

ADD . /

ENTRYPOINT [ "python", "./lava-ctl.py" ]
