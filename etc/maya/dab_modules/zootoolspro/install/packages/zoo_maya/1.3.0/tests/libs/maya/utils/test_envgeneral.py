from tests import mayatestutils
from zoo.libs.maya.utils import general


class TestEnvGeneral(mayatestutils.BaseMayaTest):
    def test_pluginQuery(self):
        self.loadPlugin("zooundo.py")
        self.assertTrue(general.isPluginLoaded("zooundo.py"))
