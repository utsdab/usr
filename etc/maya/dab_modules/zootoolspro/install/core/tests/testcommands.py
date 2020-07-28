import os
import pprint
import tempfile
from basetest import BaseTest


class TestZooConfig(BaseTest):
    def setUp(self):
        pprint.pprint(os.environ.items())
        from zoo.core import api
        self.api = api
        self.zooConfig = api.zooFromPath(os.environ["ZOOTOOLS_ROOT"])

    def testCreatePackage(self):
        outputDir = self._testFolder
        packagepath = os.path.join(outputDir, "testPackage")
        args = ["--destination", packagepath, "--name", "myPackage", "--author", "sparrow", "--displayName",
                "my Package"]
        self.zooConfig.runCommand("createPackage",
                                  arguments=args)
        self.assertTrue(os.path.exists(packagepath))
        self.assertTrue(os.path.exists(os.path.join(packagepath, "zoo_package.json")))
