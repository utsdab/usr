import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class BaseTest(unittest.TestCase):
    _testFolder = ""
    _mayaFolder = ""
    _pathsToRemove = set()
    _originalEnv = {}

    @classmethod
    def _runSetup(cls, batFile):
        tempDir = tempfile.mkdtemp("zootoolstests")
        cls._pathsToRemove.add(tempDir)
        projectFolder = os.path.join(tempDir, "zootoolspro")
        mayaFolder = os.path.join(tempDir, "maya")
        process = subprocess.Popen(" ".join([batFile,
                                             "setup", "--destination", projectFolder,
                                             "--app", "maya",
                                             "--app_dir", mayaFolder
                                             ]), close_fds=True)
        process.communicate()
        os.environ["ZOOTOOLS_ROOT"] = projectFolder
        assert os.path.exists(mayaFolder)
        assert os.path.exists(projectFolder)
        return tempDir, mayaFolder

    @classmethod
    def setUpClass(cls):
        # ok we need to setup a testing area
        # we do this by running the bat --setup command to install into a temp location
        # we fake the maya install by pointing it to a subfolder
        # test structure is setup like the following
        # temp/zootolsndjnvjsb
        #           - Maya
        #           - zootoolspro
        #               - config
        #               - install
        root = os.path.dirname(os.path.dirname(__file__))
        batFile = os.path.join(root, "bin", "zoo_cmd.bat")
        logger.debug("batFile: {}".format(batFile))
        if not os.path.exists(batFile):
            raise OSError("Bat file doesn't exist: {}".format(batFile))
        tmpFile, mayaFolder = cls._runSetup(batFile)
        currentEnv = os.path.abspath(os.path.join(root, "../../config/env", "package_version.config"))
        with open(currentEnv, "r") as f:
            cls._originalEnv = json.load(f)
        pythonPath = os.path.join(tmpFile, "zootoolspro", "install", "core", "python")
        assert os.path.exists(pythonPath)
        sys.path.append(pythonPath)
        logger.debug("pythonpath: {}".format(pythonPath))
        cls._testFolder = tmpFile
        cls._mayaFolder = mayaFolder

    @classmethod
    def tearDownClass(cls):
        for path in cls._pathsToRemove:
            if os.path.exists(path):
                shutil.rmtree(path)
