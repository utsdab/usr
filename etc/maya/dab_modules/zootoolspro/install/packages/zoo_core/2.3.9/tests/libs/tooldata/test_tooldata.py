import os
import logging
import tempfile
import unittest
import shutil
from collections import OrderedDict

from zoo.libs.tooldata import tooldata
logger = logging.getLogger(__name__)


class TestToolData(unittest.TestCase):
    rootOne = ""
    rootTwo = ""
    rootThree = ""

    @classmethod
    def setUpClass(cls):
        cls.rootOne = tempfile.mkdtemp()
        cls.rootTwo = tempfile.mkdtemp()
        cls.rootThree = tempfile.mkdtemp()

    def setUp(self):
        self.toolset = tooldata.ToolSet()
        self.roots = OrderedDict({"internal": self.rootOne,
                                  "user": self.rootTwo,
                                  "network": self.rootThree})
        self.workspaceSetting = "prefs/hotkeys/workspace1"
        self.shaderEditorSetting = "prefs/tools/shaderEditor/uiState.json"

    def _bindRoots(self):
        for name, root in self.roots.items():
            self.toolset.addRoot(root, name)

    def test_addRoots(self):
        self._bindRoots()
        self.assertEquals(len(self.toolset.roots.keys()), 3)

        # check to make sure order is kept
        for i in range(len(self.roots.keys())):
            testRoot = self.roots[self.roots.keys()[i]]
            self.assertTrue(self.toolset.roots[self.toolset.roots.keys()[i]], testRoot)
        with self.assertRaises(tooldata.RootAlreadyExistsError):
            self.toolset.addRoot(self.toolset.root("internal"), "internal")

    def test_createSetting(self):
        self.toolset.addRoot(self.roots["user"], "user")
        toolsSetting = self.toolset.createSetting(self.workspaceSetting, root="user",
                                                  data={"testdata": {"bob": "hello"}})
        self.assertEquals(self.toolset.rootNameForPath(toolsSetting.rootPath()), "user")
        toolsSetting.save()
        self.assertTrue(toolsSetting.path().exists(), msg="Path doesn't exist: {}".format(str(toolsSetting.path())))
        self.assertTrue(self.toolset.findSetting(self.workspaceSetting, root="user").isValid())
        newSettings = self.toolset.open(toolsSetting.root, toolsSetting.relativePath)
        self.assertEquals(newSettings["relativePath"], toolsSetting["relativePath"])
        self.assertEquals(newSettings["root"], toolsSetting["root"])
        self.assertEquals(newSettings["testdata"], {"bob": "hello"})

    @classmethod
    def tearDownClass(cls):
        for i in (cls.rootOne,
                  cls.rootTwo,
                  cls.rootThree):
            if os.path.exists(i):
                shutil.rmtree(i)
