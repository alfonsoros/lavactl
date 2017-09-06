import unittest
import tempfile
from ConfigParser import ConfigParser
from config.default import DefaultConfig
from atf import AtfImage


class TestAtfImage(unittest.TestCase):

    def test_ConstructDefaultAtfImage(self):
        img = AtfImage()
        default = DefaultConfig()
        self.assertEqual(img._server, default.get('artifactory', 'server'))
        self.assertEqual(img._latest, default.get('artifactory', 'latest'))
        self.assertEqual(img._kernel, default.get('artifactory', 'kernel'))
        self.assertEqual(img._rootfs, default.get('artifactory', 'rootfs'))

    def test_ConstructAtfImageWithUserAndPassword(self):
        conf = DefaultConfig()
        conf.set("artifactory", "user", "test_user")
        conf.set("artifactory", "pass", "test_pass")
        img = AtfImage(conf)
        self.assertEqual(img.user, conf.get('artifactory', 'user'))
        self.assertEqual(img.password, conf.get('artifactory', 'pass'))
        self.assertTrue(img.auth() is not None)
