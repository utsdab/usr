__all__ = ["Environment"]

import glob
import os
import logging
from zoovendor import pathlib2
from zoo.core import constants
from zoo.core.packageresolver import package
from zoo.core.util import filesystem
from zoo.core import errors

logger = logging.getLogger(__name__)


class Environment(object):

    def __init__(self, zooConfig):
        """
        :param zooConfig: The zoo configuration instance
        :type zooConfig: :class:`zoo.core.manager.Zoo`
        """
        self.zooConfig = zooConfig
        self.cache = {}  # type: dict[str: package.Package]

    def _environmentPath(self):
        """Internal function which handles discovery of the environment path for zoo configuration.

        :return: The Path object representing the absolute path.
        :rtype: :class:`pathlib2.Path`
        """
        definedPath = os.getenv(constants.ZOO_PKG_VERSION_PATH, "")
        if not os.path.isfile(definedPath):
            return pathlib2.Path(os.path.join(self.zooConfig.configPath, "env", "package_version.config"))
        environmentPath = pathlib2.Path(definedPath)
        environmentPath = environmentPath.resolve()
        if environmentPath.exists():
            return environmentPath

        return pathlib2.Path(self.zooConfig.configPath) / "env" / "package_version.config"

    def environmentPath(self):
        """The environment config path on disk

        :return: The package_version.config file path
        :rtype: str
        """
        configPath = self._environmentPath()

        if configPath.exists():
            return str(configPath)
        raise errors.MissingEnvironmentPath("Environment Config file doesn't "
                                            "exists at location: {}".format(configPath))

    def loadEnvironmentFile(self):
        """Method which loads the environment File

`        Internal use only.
`
        :return: The json data from the environment File.
        :rtype: dict
        """
        envPath = self.environmentPath()
        logger.debug("Loading environment: {}".format(envPath))
        envData = filesystem.loadJson(str(envPath))
        for n, info in envData.items():
            info["name"] = n
        return envData

    def updateEnvironmentDescriptorFromDict(self, descriptor):
        """Update's The currently load environment with the provided descriptor dict.

        :param descriptor: The descriptor dict in the same format as the environment data
        :type descriptor: dict
        """
        desc = dict(descriptor)
        name = descriptor["name"]
        del desc["name"]
        desc = {name: desc}
        envPath = self._environmentPath()
        try:
            envData = self.loadEnvironmentFile()
            envData.update(desc)
        except errors.MissingEnvironmentPath:
            self.createEnvironmentFile(desc)
            return

        logger.debug("Updating Environment: {} with: {}".format(envPath, descriptor))
        filesystem.saveJson(envData, str(envPath), indent=4, sort_keys=True)

    def removeDescriptorFromEnvironment(self, descriptor):
        """Remove's the provided descriptor instance from the currently loaded environment.

        :param descriptor: The descriptor instance to delete.
        :type descriptor: :class:`descriptor.Descriptor`
        :return: True if deleting the descriptor was successful.
        :rtype: bool
        """
        try:
            envData = self.loadEnvironmentFile()
        except errors.MissingEnvironmentPath:
            raise
        try:
            del envData[descriptor.name]
        except KeyError:
            logger.error("Descriptor: {} doesn't exist in current environment")
            raise
        filesystem.saveJson(envData, str(self._environmentPath()), indent=4, sort_keys=True)
        return True

    def createEnvironmentFile(self, env=None):
        """Creates an Environment file with the corresponding package data if the
        File doesn't already exist.

        Location of the environment file::

            zooRootPath/config/env/package_version.config

        :return: True if the environment file was created
        :rtype: bool
        """
        env = env or {}
        configPath = os.path.join(self.zooConfig.configPath,
                                  "env",
                                  "package_version.config")
        if not os.path.exists(configPath):
            logger.debug("Creating new environment file: {}".format(configPath))
            filesystem.saveJson(env, configPath, indent=4, sort_keys=True)
            return True
        return False

    def resolveFromPath(self, requestPath, **kwargs):
        try:
            requests = filesystem.loadJson(requestPath)
        except ValueError:
            logger.error("Request json path has incorrect syntax: {}".format(requestPath),
                         exc_info=True)
            raise
        return self.resolve(requests, **kwargs)

    def resolve(self, requestsInfo, apply=True):
        resolved = set()
        logger.debug("Beginning resolve of requested packages: {}".format(requestsInfo))
        for packageName, rawDescriptor in requestsInfo.items():
            rawDescriptor["name"] = packageName
            pkgDescriptor = self.zooConfig.descriptorFromDict(rawDescriptor)
            existingPkg = None
            # we only need to resolve non local path i.e git
            if pkgDescriptor.type != pkgDescriptor.LOCAL_PATH:
                existingPkg = self.cache.get(package.Package.nameForPackageNameAndVersion(packageName,
                                                                                          pkgDescriptor.version))
            # if we already have a package, make sure it's been resolved to the
            # current env
            if existingPkg:
                if not existingPkg.resolved and apply:
                    existingPkg.resolve(applyEnvironment=apply)
                resolved.add(existingPkg)
                continue
            # package doesn't exist on disk so resolve it through the descriptor
            valid = pkgDescriptor.resolve()
            if valid:
                if apply:
                    pkgDescriptor.package.resolve(applyEnvironment=apply)
                self.cache[str(pkgDescriptor.package)] = pkgDescriptor.package
                resolved.add(pkgDescriptor.package)
        _patchReloadZooNamespacePackage()
        # loop all the resolved packages and run the startup script
        # the startup script for a package allows the developer to run logic
        # just before zootools fully loads but contains all packages ie. copy preferences etc
        visited = set()
        for pkgName, pkg in self.cache.items():
            dependencies = pkg.requirements
            for dependency in dependencies:
                dependentPkg = self.packageByName(dependency)
                if dependentPkg and str(dependentPkg) not in visited:
                    dependentPkg.runStartup()
                    visited.add(str(dependentPkg))
            if str(pkg) not in visited:
                pkg.runStartup()
                visited.add(str(pkg))

        return resolved

    def shutdown(self):
        visited = set()
        for pkgName, pkg in self.cache.items():
            dependencies = pkg.requirements
            for dependency in dependencies:
                dependentPkg = self.packageByName(dependency)
                if dependentPkg and str(dependentPkg) not in visited:
                    dependentPkg.shutdown()
                    visited.add(str(dependentPkg))
            if str(pkg) not in visited:
                pkg.shutdown()
                visited.add(str(pkg))

    def packageFromPath(self, path):
        """Returns a :class:`Package` instance or None from the given path.

        The path can either be the directory containing the package or the zoo_package.json file.

        :param path: The directory or the zoo_package.json absolute path
        :type path: str
        :return:
        :rtype: :class:`Package`
        """
        if path.endswith(constants.PACKAGE_NAME):
            return package.Package(path)
        packageJson = os.path.join(path, constants.PACKAGE_NAME)
        if os.path.exists(packageJson):
            return package.Package(packageJson)

    def packageForDescriptor(self, descriptor):
        if descriptor.isDescriptorOfType(descriptor.LOCAL_PATH):
            paths = [os.path.join(descriptor.path, constants.PACKAGE_NAME)]
        else:
            paths = self._searchForPackage(descriptor.name, descriptor.version)
        if paths:
            pkg = package.Package(paths[0])
            return self.cache.get(str(pkg), pkg)

    def _searchForPackage(self, packageName, packageVersion):
        return glob.glob(os.path.join(self.zooConfig.packagesPath,
                                      packageName,
                                      str(packageVersion),
                                      constants.PACKAGE_NAME))

    def existingPackage(self, pkg):
        cachedPackage = self.cache.get(str(pkg))
        if cachedPackage is not None:
            return cachedPackage
        packageLocations = self._searchForPackage(pkg.name, pkg.version)
        if packageLocations:
            # in this case the package already exists so first cache it then return it
            pkg = package.Package(packageLocations[0])
            self.cache[str(pkg)] = pkg
            return pkg

    def packageByName(self, packageName):
        """Finds the package from the cache by name

        """
        for pkgStr, pkg in self.cache.items():
            if pkg.name == packageName:
                return pkg

    def testPackagesInCurrentEnv(self):
        for pkgStr, pkg in self.cache.items():
            if pkg.tests:
                yield pkg.tests, pkg


def _patchReloadZooNamespacePackage():
    """Patch function to reload zoo namespace after all current packages have been loaded, this
    is to work around limitations with pythons import system since we dynamically build sys.path
    with this lib which also contains the zoo namespace.

    :note: This is for internal use only.

    :reference:
    https://stackoverflow.com/questions/9758753/how-to-import-namespaced-packages-for-which-sys-path-needs-to-be
    -adjusted
    """
    import zoo
    try:
        rel = reload  # Python 2.7
    except NameError:
        try:
            from importlib import reload as rel  # Python 3.4+

        except ImportError:
            from imp import reload as rel  # Python 3.0 - 3.3
    rel(zoo)
