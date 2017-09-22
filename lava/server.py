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

from config import ConfigManager
from utils import timeout, TimeoutError


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
                    self._logger.debug("[ZMQ]:\n%s", yaml.dump(data, default_flow_style=False))

                    # filter message from different job
                    if "job" not in data or job != data["job"]:
                        continue

                    status = data["status"]
                    self._logger.debug( "Job ID %s -- status: %s", job, status)
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
    class LavaServerError(RuntimeError):
        pass

    def __init__(self, config=None, logger=None):
        super(LavaServer, self).__init__()
        self.logger = logger or logging.getLogger(__name__ + '.LavaServer')
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

        if not job_id:
            self.logger.error("Error at submitting the LAVA job")
            raise LavaServerError("Couldn't submit the job to the LAVA master")
        else:
            self.logger.debug("Successfully submitted job -- id: %s", job_id)

        return job_id

    def status(self, job_id):
        """Return the status of the corresponding job ID"""
        return self._rpc.scheduler.job_status(str(job_id))

    def submit_and_wait(self, job):
        """Submit the job and return a JobListener """
        job_id = self.submit(job)

        if isinstance(job_id, list):
            job_id = int(float(job_id[0]))

        listener = JobListener(self._pub_url, logger=self.logger)
        success = listener.wait(job_id, seconds=self._timeout)
        return success


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
