# -*- coding: utf-8 -*-
"""
Copyright (c) 2017 Siemens AG
Author: Alfonso Ros Dos Santos

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import Queue
import gzip
import logging
import os
import sys
import paramiko
import shutil
import signal
import hashlib
import socket
import xmlrpclib
import yaml
import zmq
import urllib2
import stat

from progress.bar import Bar

from lava_ctl.config import ConfigManager
from lava_ctl.utils import timeout, TimeoutError


class JobListener(object):
    """Listens for the ZMQ notifications coming from the LAVA publisher.

    Callbacks can be register for precessing messages

    """
    FINISHED_JOB_STATUS = ["Complete", "Incomplete", "Canceled"]

    def __init__(self, url, logger=None):
        super(JobListener, self).__init__()
        self._logger = logger or logging.getLogger(__name__ + '.JobListener')
        self._ctx = zmq.Context.instance()
        self._sub = self._ctx.socket(zmq.SUB)
        self._sub.setsockopt(zmq.SUBSCRIBE, b"")
        self._sub.connect(url)

    def wait(self, job, seconds=None):
        def loop():
            while True:
                try:
                    msg = self._sub.recv_multipart()
                    (topic, uuid, dt, username, data) = msg[:]

                    data = yaml.safe_load(data)
                    self._logger.debug("[ZMQ]:\n%s", yaml.dump(
                        data, default_flow_style=False))

                    # filter message from different job
                    if "job" not in data or job != data["job"]:
                        continue

                    status = data["status"]
                    self._logger.debug("Job ID %s -- status: %s", job, status)
                except Exception:
                    status = None

                if status and status in self.FINISHED_JOB_STATUS:
                    return True if status == "Complete" else False

        try:
            wait = timeout(seconds=seconds)(loop)
            return wait()
        except TimeoutError:
            return False


class LavaServer(object):
    """Handle the communication with the LAVA Master server

    This class requires the user to define the following configuration
    parameters:

      lava.server.addr
      lava.server.port
      lava.server.files_prefix
      lava.server.user
      lava.server.token

    ENVIRONMENT:

    You can use the LAVA_USER and LAVA_TOKEN environment variables to set the
    corresponding required variables.

      LAVA_USER -> lava.server.user
      LAVA_TOKEN -> lava.server.token

    """
    class LavaServerError(RuntimeError):
        pass

    def __init__(self, config=None, logger=None):
        super(LavaServer, self).__init__()
        self._logger = logger or logging.getLogger(__name__ + '.LavaServer')
        self.read_config(config or ConfigManager())

    def read_config(self, config):
        """Read the relevant configuration parameters

        The following are the relevant parameters for the connection with the lava
        master:

          - lava.server.host
          - lava.server.port
          - lava.server.user
          - lava.server.token

        """
        ENVIRONMENT_PARAMETERS = {
            'LAVA_HOST': 'lava.server.host',
            'LAVA_PORT': 'lava.server.port',
            'LAVA_PUBLISHER_PORT': 'lava.publisher.port',
            'LAVA_USER': 'lava.server.user',
            'LAVA_TOKEN': 'lava.server.token',
        }

        REQUIRED_PARAMETERS = [
            'lava.server.host',
            'lava.server.port',
            'lava.server.user',
            'lava.server.token',
            'lava.publisher.port',
        ]

        # Check environment variables
        for env, param in ENVIRONMENT_PARAMETERS.iteritems():
            if env in os.environ:
                config.set(param, os.environ[env])

        # Check if the required parameters are available
        for param in REQUIRED_PARAMETERS:
            if not config.has(param):
                self._logger.error("Missing parameter %s", param)
                raise RuntimeError("Missing configuration", param)

        host = config.get('lava.server.host')
        port = int(config.get('lava.server.port'))
        user = config.get('lava.server.user')
        token = config.get('lava.server.token')

        self._base_url = "http://%s:%s/" % (host, port)
        self._url = "http://%s:%s@%s:%s/" % (user, token, host, port)

        rpcurl = self._url + 'RPC2'
        self._logger.debug('LAVA Master XML-RPC: %s', rpcurl)
        self._rpc = xmlrpclib.ServerProxy(rpcurl)

        # Store the publisher url
        self._pub_url = 'tcp://%s:%s' % (host,
                                         int(config.get('lava.publisher.port')))

        # timeout for the job
        self._timeout = int(config.get('lava.server.jobs.timeout'))

        try:
            version = self._rpc.system.version()
            self._logger.debug('Connected to LAVA Master')
            self._logger.debug('LAVA Master VERSION %s', version)
        except xmlrpclib.ProtocolError, err:
            self._logger.error('Error while connecting to LAVA Master - %s %s',
                               err.errcode, err.errmsg)
            raise err

    def validate(self, job_definition):
        """Validate a job definition"""
        try:
            self._rpc.scheduler.validate_yaml(str(job_definition))
            self._logger.debug("Job definition validated")
            return True
        except xmlrpclib.Fault, flt:
            self._logger.error("Job validation error - %s %s",
                               flt.faultCode, flt.faultString)
            return False
        except xmlrpclib.ProtocolError, err:
            self._logger.error('Error while connecting to LAVA Master - %s %s',
                               err.errcode, err.errmsg)
            raise err

    def check_tests_results(self, job):
        """Check if all the tests of a job are passed"""
        report = yaml.load(self._rpc.results.get_testjob_results_yaml(job))
        results = [test.get('result') for test in report]
        self._logger.info("PASSED %d", results.count('pass'))
        self._logger.info("FAILED %d", results.count('fail'))
        return all(result == "pass" for result in results)

    def submit(self, job_definition, wait=True):
        """Submit a job to the LAVA server"""
        job_id = self._rpc.scheduler.submit_job(str(job_definition))

        if not job_id:
            self._logger.error("Error at submitting the LAVA job")
            raise LavaServerError("Couldn't submit the job to the LAVA master")
        else:
            self._logger.info("Successfully submitted job -- id: %s", job_id)

            if isinstance(job_id, list):
                baseid = int(float(job_id[0]))
                for i in xrange(len(job_id)):
                    self._logger.info("Job %s output:\n%s/scheduler/job/%s",
                                      job_id[i], self._base_url, baseid + i)
            else:
                self._logger.info("Job output:\n%s/scheduler/job/%s",
                                  self._base_url, job_id)

        if isinstance(job_id, list):
            job_id = int(float(job_id[0]))

        if wait:
            listener = JobListener(self._pub_url, logger=self._logger)
            success = listener.wait(job_id, seconds=self._timeout)
            return success and self.check_tests_results(job_id)
        else:
            return True

    def status(self, job_id):
        """Return the status of the corresponding job ID"""
        return self._rpc.scheduler.job_status(str(job_id))
