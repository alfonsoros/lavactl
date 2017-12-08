# Copyright (c) 2017 Siemens AG
# Author: Alfonso Ros Dos Santos

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

FROM python:2.7

ARG user
ARG token
ARG master_addr
ARG ftp_user
ARG ftp_pass
ARG ssh_priv

ENV LAVA_SERVER_ADDR=$master_addr
ENV LAVA_USER=$user
ENV LAVA_TOKEN=$token
ENV LAVA_STORAGE_FTP_USER=$ftp_user
ENV LAVA_STORAGE_FTP_PASS=$ftp_pass

ADD . /src
WORKDIR /lava-ctl

RUN pip install -e /src/
RUN (cd /src && python setup.py install)

ENTRYPOINT ["lava-ctl", "--debug"]
