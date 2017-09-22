# -*- coding: utf-8 -*-
import Queue
import gzip
import logging
import os
import paramiko
import shutil
import signal
import socket
import xmlrpclib
import yaml
import zmq

from progress.bar import Bar
from config import ConfigManager


class Timeout(object):
    """ Timeout error class with ALARM signal. Accepts time in seconds. """
    class TimeoutError(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_raise)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)

    def timeout_raise(self, *args):
        raise Timeout.TimeoutError()


class JobListener(object):
    """docstring for JobListener"""

    def __init__(self, url, logger=None):
        super(JobListener, self).__init__()
        self._logger = logger or logging.getLogger(__name__ + '.JobListener')
        self._ctx = zmq.Context.instance()
        self._sub = self._ctx.socket(zmq.SUB)
        self._sub.setsockopt(zmq.SUBSCRIBE, b"")
        self._sub.connect(url)

    def wait(self, jobs, timeout):
        """Wait for all the jobs"""

        if not isinstance(jobs, list):
            job_id = jobs
        else:
            job_id = int(float(jobs[0]))

        FINISHED_JOB_STATUS = ["Complete", "Incomplete", "Canceled"]

        try:
            with Timeout(timeout):
                while True:
                    try:
                        msg = self._sub.recv_multipart()
                        (topic, uuid, dt, username, data) = msg[:]

                        data = yaml.safe_load(data)
                        if "job" in data and job_id == data["job"]:
                            self._logger.debug(
                                "Received ZMQ message:\n%s", yaml.dump(data,
                                                                       default_flow_style=False))
                            self._logger.debug(
                                "Job ID %s -- status: %s", job_id, data["status"])
                            if data["status"] in FINISHED_JOB_STATUS:
                                self._status = data["status"]
                                self._logger.debug(
                                    "job %s finished with status %s", job_id, self._status)

                                return True

                    except IndexError:
                        continue

                return True

        except Timeout.TimeoutError:
            return False


class LavaServer(object):
    """Handle the communication with the LAVA Master server

    This class requires the user to define the following configuration
    parameters:

      lava.server:
        addr = "139.25.40.26"
        port = 2041
        files_prefix = "lava-files"
        user = LAVA_USER
        token = LAVA_TOKEN


    ENVIRONMENT:

    You can use the LAVA_USER and LAVA_TOKEN environment variables to set the
    corresponding required variables.

      LAVA_USER -> lava.server.user
      LAVA_TOKEN -> lava.server.token

    """

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

        # Check environment
        for env, param in ENVIRONMENT_PARAMETERS.iteritems():
            if env in os.environ and not config.has_option(param):
                config.set(param, os.environ[env])

        for param in REQUIRED_PARAMETERS:
            if not config.has_option(param):
                self.logger.error("Missing parameter %s", param)
                raise RuntimeError("Missing configuration", param)

        host = config.get('lava.server.host')
        port = config.get('lava.server.port')
        user = config.get('lava.server.user')
        token = config.get('lava.server.token')
        url = "http://%s:%s@%s:%s/RPC2" % (user, token, host, port)
        self.logger.debug('LAVA Master XML-RPC: %s', url)
        self._rpc = xmlrpclib.ServerProxy(url)

        # Store the publisher url
        self._pub_url = 'tcp://%s:%s' % (host,
                                         config.get('lava.publisher.port'))

        # timeout for the jobs
        self._timeout = config.get('lava.jobs.timeout')

        try:
            version = self._rpc.system.version()
            self.logger.debug('Connected to LAVA Master')
            self.logger.debug('LAVA Master VERSION %s', version)
        except xmlrpclib.ProtocolError, err:
            self.logger.error('Error while connecting to LAVA Master - %s %s',
                              err.errcode, err.errmsg)
            raise err

    def validate(self, job_definition):
        try:
            self._rpc.scheduler.validate_yaml(str(job_definition))
            self._logger.debug("Job definition validated")
            return True
        except xmlrpclib.Fault, flt:
            self.logger.error("Job validation error - %s %s",
                              flt.faultCode, flt.faultString)
            return False
        except xmlrpclib.ProtocolError, err:
            self.logger.error('Error while connecting to LAVA Master - %s %s',
                              err.errcode, err.errmsg)
            raise err

    def submit(self, job_definition):
        job_id = self._rpc.scheduler.submit_job(str(job_definition))
        # check the job id is fine
        return job_id

    def status(self, job_id):
        """Return the status of the corresponding job ID"""
        return self._rpc.scheduler.job_status(str(job_id))

    def submit_and_wait(self, job):
        """Submit the job and return a JobListener """
        job_id = self.submit(job)
        listener = JobListener(self._pub_url, logger=self.logger)
        return listener.wait(job_id, timeout=self._timeout)

    def __init__(self, config=None, logger=None):
        super(LavaServer, self).__init__()
        self.logger = logger or logging.getLogger(__name__ + '.LavaServer')
        self.read_config(config or ConfigManager())


class Storage(object):

    def __init__(self, config=None):
        if not config:
            config = DefaultConfig()

        self._logger = logging.getLogger(__name__)
        self._logger.progress_bar = config.getboolean(
            'logging', 'progress-bars')

        server = config.get('lava.server', 'addr')
        port = config.getint('lava.sftp', 'port')
        usr = config.get('lava.sftp', 'user')
        pwd = config.get('lava.sftp', 'pass')

        self._transport = paramiko.Transport((server, port))
        self._transport.connect(username=usr, password=pwd)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        self._download_url = config.get('lava.server', 'files')

    def __str__(self):
        return u'Lava master ftp storage'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._sftp.close()
        self._transport.close()

    def upload(self, path, compressed=False):
        # Try to compress the file before uploading
        if compressed and not path.endswith('.gz'):
            self._logger.info('Gzip the filesystem before uploading')
            with open(path, 'rb') as f_in, gzip.open(path + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            path = path + '.gz'

        # Some fancy progress bar
        bar = Bar('Uploading %s' % os.path.basename(path))

        def update_progress(current, total):
            bar.index = current
            bar.max = total
            bar.update()

        if not self._logger.progress_bar:
            update_progress = None

        name = os.path.basename(path)
        self._sftp.put(path, name, callback=update_progress)
        bar.finish()
        return u'%s/%s' % (self._download_url, name)
