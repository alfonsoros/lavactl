import unittest
import tempfile
from jobs import JobDefinition, Job


class TestJobDefinition(unittest.TestCase):

    def setUp(self):
        self.file = tempfile.NamedTemporaryFile()
        self.file.write("""
---
lava:
  job:
    name: "test"
""")
        self.file.seek(0)

    def tearDown(self):
        self.file.close()

    def test_ConstructJobDescriptionFromYAMLFile(self):
        jd = JobDefinition(filename=self.file.name)
        self.assertEqual(jd.get("lava.job.name"), "test")

class TestJob(unittest.TestCase):

    @unittest.skip("job is broken now")
    def test_EmptyConfigurationCantBeSubmitted(self):
      job = Job({})
      self.assertFalse(job.valid())
