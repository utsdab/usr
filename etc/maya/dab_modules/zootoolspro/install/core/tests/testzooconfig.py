import os

from basetest import BaseTest


class TestZooConfig(BaseTest):
    def setUp(self):
        from zoo.core import api
        self.api = api
        self.zooConfig = api.zooFromPath(os.environ["ZOOTOOLS_ROOT"])

    def testHasCorrectEnvPaths(self):
        self.assertTrue(os.path.exists(self.zooConfig.rootPath))
        self.assertEqual(self.zooConfig, self.api.currentConfig())
        self.assertTrue(self.zooConfig.configPath.endswith("config"),
                        msg="Config Folder Doesn't end with 'config', {}".format(self.zooConfig.configPath))
        self.assertTrue(self.zooConfig.corePath.endswith("core"),
                        msg="core Folder Doesn't end with python', {}".format(self.zooConfig.corePath))

        self.assertTrue(self.zooConfig.packagesPath.endswith("packages"),
                        msg="Package Folder Doesn't end with 'packages', {}".format(self.zooConfig.packagesPath))
        self.assertTrue(os.path.exists(self.zooConfig.configPath),
                        msg="Config Folder Doesn't exist, {}".format(self.zooConfig.configPath))
        self.assertTrue(os.path.exists(self.zooConfig.corePath),
                        msg="core Folder Doesn't exist, {}".format(self.zooConfig.corePath))
        self.assertTrue(os.path.exists(self.zooConfig.packagesPath),
                        msg="Package Folder Doesn't exist, {}".format(self.zooConfig.packagesPath))
        self.assertTrue(os.path.exists(os.path.join(self._mayaFolder, "zootoolspro.mod")),
                        msg="maya module Folder Doesn't exist, {}".format(os.path.join(self._mayaFolder,
                                                                                       "zootoolspro.mod")))

    def testCreateEnvironmentFile(self):
        # grab the current env and rename it so we dont fuck it
        # now create the new env and test it's existence
        # now delete the new one and rename the old back again
        originalEnvFile = self.zooConfig.resolver.environmentPath()
        newPath = os.path.join(os.path.dirname(originalEnvFile), "testEnv.config")
        os.rename(originalEnvFile, newPath)
        self.zooConfig.resolver.createEnvironmentFile({})
        self.assertTrue(os.path.exists(newPath))
        os.remove(self.zooConfig.resolver.environmentPath())
        os.rename(newPath, originalEnvFile)

    def testLoadEnvironmentFile(self):
        self.assertIsInstance(self.zooConfig.resolver.loadEnvironmentFile(), dict)

    def testSetupCommand(self):
        """While the base class setupClass() handles installing zootools into a temp
        Folder, this is normally run from the bare repo which isn't installed.

        So here we run the setup again but this time from the new location
        """

        batFile = os.path.join(self.zooConfig.corePath, "bin", "zoo_cmd.bat")
        if not os.path.exists(batFile):
            raise OSError("Bat file doesn't exist: {}".format(batFile))
        self._runSetup(batFile)

    def testIsAdmin(self):
        self.assertFalse(self.zooConfig.isAdmin)
        self.zooConfig.isAdmin = True
        self.assertTrue(self.zooConfig.isAdmin)

    def testShutdown(self):
        self.zooConfig.shutdown()
        self.assertIsNone(self.api.currentConfig())
        self.zooConfig = self.api.zooFromPath(os.environ["ZOOTOOLS_ROOT"])
        self.assertIsNotNone(self.api.currentConfig())

    def testInstallUpdateEnvironment(self):
        for k,v in self._originalEnv.items():
            v["name"] = k
            break
        envDict = v
        self.zooConfig.resolver.updateEnvironmentDescriptorFromDict(envDict)
        self.zooConfig.resolver.resolveFromPath(self.zooConfig.resolver.environmentPath())
        self.assertTrue(len(list(self.zooConfig.resolver.cache.keys()))== 1)

        package = self.zooConfig.resolver.cache[list(self.zooConfig.resolver.cache.keys())[0]]
        descriptorInstance = self.zooConfig.descriptorForPackageName(package.name)
        # local imports are used due to zoo requiring bootstrapping otherwise configuration don't exist.
        from zoo.core.descriptors import descriptor
        self.assertIsNotNone(descriptorInstance)
        self.assertIsInstance(descriptorInstance, descriptor.Descriptor)
        resolvedDescriptor = self.zooConfig.descriptorFromDict(descriptorInstance.serialize())
        self.assertEqual(resolvedDescriptor, descriptorInstance)
