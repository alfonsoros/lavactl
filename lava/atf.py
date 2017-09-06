import logging

from artifactory import ArtifactoryPath
from config.default import DefaultConfig


class AtfImage(object):
    """Artifactory Lastest Image for testing

      The Images stored in the artifactory can be used to run Tests.

      To authenticate with the artifactory, it is possible to either set the
      environment variables:

        - ATF_USER : username for the artifactory site
        - ATF_PASS : password for the user

      or add the keys to the configuration file:

        [artifactory]
        user = "username"
        pass = "pass"
        ...

      Ultimately you can use the class properties to set them:

        img = AtfImage()
        img.user = "username"
        img.password = "password"
        img.kernel_url = "https://artifactory.com/image/kernel.bin"
        img.rootfs_url = "https://artifactory.com/image/rootfs.ext4"

      If you are providing a custom configuration, remember to specify the
      required fields in the [artifactory] section:

        [artifactory]
        server = artifactory URL
        latest = Name of the latest EBSY image in the artifactory
        kernel = name of the kernel file inside the latest image
        rootfs = name for the root filesystem file inside the latest image

    """
    REQUIRED_FIELDS = ['server', 'latest', 'kernel', 'rootfs']
    OPTIONAL_FIELDS = ['user', 'pass']

    def update_artifactory_files(self):
        self._kernel_file = ArtifactoryPath(
            self._kernel_url, auth=self.auth(), verify=False)
        self._rootfs_file = ArtifactoryPath(
            self._rootfs_url, auth=self.auth(), verify=False)

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = value
        if self._pass:
            self.update_artifactory_files()

    @property
    def password(self):
        return self._pass

    @password.setter
    def password(self, value):
        self._pass = value
        if self._pass:
            self.update_artifactory_files()

    def auth(self):
        """True if the user/password credentials are available"""
        if self.user and self.password:
            self.logger.debug("atf user: %s pass: %s", self._user, self._pass)
            return (self.user, self.password)
        else:
            return None

    @property
    def kernel_url(self):
        return self._kernel_url

    @kernel_url.setter
    def kernel_url(self, value):
        self._kernel_file = ArtifactoryPath(
            value, auth=self.auth(), verify=False)
        self._kernel_url = value

    @property
    def rootfs_url(self):
        return self._rootfs_url

    @rootfs_url.setter
    def rootfs_url(self, value):
        self._rootfs_file = ArtifactoryPath(
            value, auth=self.auth(), verify=False)
        self._rootfs_url = value

    def kernel_md5(self):
        return self._kernel_file.stat().md5

    def rootfs_md5(self):
        return self._rootfs_file.stat().md5

    def init_from_config(self, config):
        """Check for the required fields in the configuration

        If the required fields are present, they are assigned as member
        variables. The required configuration files are:

          [artifactory]
          server = artifactory URL
          latest = Name of the latest EBSY image in the artifactory
          kernel = name of the kernel file inside the latest image
          rootfs = name for the root filesystem file inside the latest image

        """
        CONFIG_SECTION = "artifactory"
        REQUIRED_FIELDS = ['server', 'latest', 'kernel', 'rootfs']

        present = lambda x: config.has_option(CONFIG_SECTION, x)
        missing = [f for f in REQUIRED_FIELDS if not present(f)]
        if missing:
            self.logger.error(
                "Missing artifactory fields: %s", ",".join(missing))
            raise Exception("Missing artifactory fields", missing)

        for param in REQUIRED_FIELDS:
            setattr(self, '_' + param,
                    config.get(CONFIG_SECTION, param).strip('"'))

        # If set, use the user/password for authentication
        if config.has_option(CONFIG_SECTION, 'user') and \
            config.has_option(CONFIG_SECTION, 'pass'):
            self._user = config.get(CONFIG_SECTION, 'user')
            self._pass = config.get(CONFIG_SECTION, 'pass')
        else:
            self._user = self._pass = None

        self._kernel_url = "%s/%s/%s" % (self._server,
                                         self._latest, self._kernel)
        self._rootfs_url = "%s/%s/%s" % (self._server,
                                         self._latest, self._rootfs)
        self.logger.debug("Valid Artifactory Configuration")

    def __init__(self, config=None, logger=None):
        super(AtfImage, self).__init__()
        self.logger = logger or logging.getLogger(__name__ + '.AtfImage')

        if not config:
            self.logger.warning("using default configuration")
            self.init_from_config(DefaultConfig(logger=self.logger))
        else:
            self.init_from_config(config)

        # The SSL verification is always disabled
        self._kernel_file = ArtifactoryPath(
            self._kernel_url, auth=self.auth(), verify=False)
        self._rootfs_file = ArtifactoryPath(
            self._rootfs_url, auth=self.auth(), verify=False)
