import os
import shutil
import stat
import tempfile
import logging

from zoo.core.util import git
from zoo.core import errors

# most users wont have gitpython install so this import would fail
# This important would work under a dev env though.
# It's the responsibility of our code to ensure the
# necessary errors occurs
try:
    from zoo.core.util.git import gitwrapper
except ImportError as imper:
    gitwrapper = None

logger = logging.getLogger(__name__)


def _handleDeleteError(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def descriptorFromCurrentConfig(config, name):
    """Returns the descriptor from the existing cached config environment.

    :param config: The zoo config  instance
    :type config: :class`zoo.core.manager.Zoo`
    :param name: The name of the Descriptor.
    :type name: str
    :return:
    :rtype: :class:`Descriptor`
    """
    for descrName, descriptorDict in config.resolver.loadEnvironmentFile().items():
        if descrName == name:
            return descriptorFromDict(config, descriptorDict)


def descriptorFromPath(config, location, descriptorInfo):
    """Returns the matching Descriptor object for the given path.

    :param config: The current config instance
    :type config: :class:`zoo.core.Zoo`
    :param location: The location of the package, can be any of the paths \
    supported by our descriptors. i.e a .git path, physical path etc
    :type location: str
    :param descriptorInfo: Descriptor dic see :class:`Descriptor` for more info.
    :type descriptorInfo: dict
    :return:
    :rtype: :class:`Descriptor`
    :raise: NotImplementedError
    """
    if location.endswith(".git") and not os.path.exists(location):
        descriptorInfo.update({"type": "git"})
        # git location
        return GitDescriptor(config,
                             descriptorInfo
                             )
    elif os.path.exists(location):
        # because the requested path is a physical
        # location we can parse the package and compose the descriptor
        # dict ourselves.
        pkg = config.resolver.packageFromPath(location)
        if not pkg:
            raise errors.InvalidPackagePath(location)
        descriptorInfo.update({"name": pkg.name,
                               "version": str(pkg.version),
                               "path": location,
                               "type": "path"})
        # physical path on disk
        return PathDescriptor(config,
                              descriptorInfo)
    raise NotImplementedError("We don't currently support descriptor: {}".format(location))


def descriptorFromDict(config, info):
    requestedType = info.get("type")
    logger.debug("Resolve descriptor for requested info: {}".format(info))
    if requestedType == Descriptor.ZOOTOOLS:
        return ZooDescriptor(config,
                             descriptorDict=info
                             )
    elif requestedType == Descriptor.LOCAL_PATH:
        return PathDescriptor(config,
                              descriptorDict=info)
    elif requestedType == Descriptor.GIT:
        return GitDescriptor(config,
                             descriptorDict=info
                             )

    raise NotImplementedError("Descriptor not supported: {}".format(info))


class Descriptor(object):
    # descriptor type constants
    GIT = "git"
    LOCAL_PATH = "path"
    ZOOTOOLS = "zootools"
    # class variables cache
    requiredkeys = ()

    def isDescriptorOfType(self, descriptorType):
        return self.type == descriptorType

    def __init__(self, config, descriptorDict):
        self.config = config
        self._descriptorDict = descriptorDict
        self.type = descriptorDict["type"]
        self.name = descriptorDict.get("name")
        self.version = ""
        self.package = None
        self._validate(descriptorDict)

    def serialize(self):
        return self._descriptorDict

    def __eq__(self, other):
        otherdict = other.serialize()
        return all(v == otherdict.get(k) for k, v in self.serialize().items())

    def __ne__(self, other):
        otherdict = other.serialize()
        return not any(v != otherdict.get(k) for k, v in self.serialize().items())

    def __repr__(self):
        return "<{}> Name: {}, Type: {}".format(self.__class__.__name__, self.name, str(self.type))

    def _validate(self, descriptorDict):
        keys = set(descriptorDict.keys())
        requiredSet = set(self.requiredkeys)
        if not requiredSet.issubset(keys):
            missingKeys = requiredSet.difference(keys)
            raise errors.DescriptorMissingKeys("<{}>: {} Missing required Keys: {}".format(self.__class__.__name__,
                                                                                           self.name,
                                                                                           missingKeys))
        return True

    def resolve(self, *args, **kwargs):
        raise NotImplementedError()

    def install(self, **arguments):
        raise NotImplementedError()

    def uninstall(self, remove=False):
        if self.package is None:
            logger.debug("Descriptor: {} has no resolved package".format(self.name))
            return False
        pkgRoot = self.package.root
        self.config.resolver.removeDescriptorFromEnvironment(self)
        if remove:
            self.package.delete()
            versionedPackageDir = os.path.dirname(pkgRoot)
            if len(os.listdir(versionedPackageDir)) == 0:
                os.rmdir(versionedPackageDir)

        return True


class ZooDescriptor(Descriptor):
    """Zoo distributable descriptor
    """
    requiredKeys = ("version", "name", "type")

    def __init__(self, config, descriptorDict):
        super(ZooDescriptor, self).__init__(config, descriptorDict)
        self.version = descriptorDict["version"]

    def resolve(self, *args, **kwargs):
        logger.debug("Resolving zootools descriptor: {}-{}".format(self.name, self.version))
        existingPackage = self.config.resolver.packageForDescriptor(self)
        if not existingPackage:
            raise errors.MissingPackageVersion("Missing package: {}".format(self.name))
        self.package = existingPackage
        return True

    def install(self, **arguments):
        if self.package:
            logger.debug("Package: {} already exists, skipping install".format(self.name))
            # self.as
            # self.config.resolver.bakePackageToEnv(self.package)
            return True
        raise NotImplementedError("We Don't currently support downloading internal packages")


class GitDescriptor(Descriptor):
    requiredkeys = ("type", "version", "path")

    def __init__(self, config, descriptorDict):
        super(GitDescriptor, self).__init__(config, descriptorDict)
        self.package = None
        self.path = descriptorDict["path"]
        self.version = descriptorDict["version"]

    def resolve(self, *args, **kwargs):
        # a support git path must end with '.git'
        if not self.path.endswith(".git"):
            raise SyntaxError("Supplied git path doesn't end with '.git'")
        # for git to successfully download and so we can early out of the download
        # we require the version and name along with the git path
        # this way we don't needlessly download the repo
        if all(i is not None for i in (self.version, self.name)):
            pkg = self.config.resolver.packageForDescriptor(self)
            # if the package already exists cache the package so the install
            # method will early out.
            if pkg is not None:
                self.package = pkg
                logger.warning("Package already exists: {}-{}".format(self.name, self.version))
                raise errors.PackageAlreadyExists(pkg)
        return True

    def install(self, **arguments):
        if self.package is not None or self.version is None:
            return
        # grab a temp folder
        localFolder = tempfile.mkdtemp("zoo_git")
        gitFolder = os.path.join(localFolder, os.path.splitext(os.path.basename(self.path))[0])
        # ensure we have git install
        try:
            git.hasGit()
        except Exception:
            raise
        if gitwrapper is None:
            logger.error("Current environment doesn't have gitpython installed")
            raise errors.MissingGitPython()

        try:
            logger.debug("Cloning Path: {} to: {}".format(self.path, gitFolder))
            repo = gitwrapper.RepoChecker.clone(self.path, localFolder)
            repo.checkout(self.version)
        except Exception:
            shutil.rmtree(localFolder, onerror=_handleDeleteError)
            raise
        package = self.config.resolver.packageFromPath(repo.repoPath)
        if package is None:
            shutil.rmtree(localFolder, onerror=_handleDeleteError)
            raise ValueError("Git Repo is not a zootools repo cancelling!")
        exists = self.config.resolver.existingPackage(package)
        if exists is not None:
            shutil.rmtree(localFolder, onerror=_handleDeleteError)
            self.package = exists
            raise ValueError("Package already exists: {}".format(str(exists)))

        self.name = package.name
        self.package = package
        destination = os.path.join(self.config.packagesPath, self.name, str(self.package.version))
        # ok we have finished download the git repo now copy it make sure its a package
        installedPackage = package.copyTo(package,
                                          destination
                                          )
        # now clean up
        shutil.rmtree(localFolder, onerror=_handleDeleteError)
        # now make sure the environment is update to date
        self.config.resolver.cache[str(installedPackage)] = installedPackage
        self._descriptorDict["type"] = "zootools"
        del self._descriptorDict["path"]
        self.config.resolver.updateEnvironmentDescriptorFromDict(self._descriptorDict)
        return True


class PathDescriptor(Descriptor):
    requiredkeys = ("name", "type", "path")

    def __init__(self, config, descriptorDict):
        super(PathDescriptor, self).__init__(config, descriptorDict)
        self.package = None
        self.path = descriptorDict["path"]

    def resolve(self):
        # a path descriptor only contains a path so we need to first resolve
        # the package inside
        package = self.config.resolver.packageFromPath(self.path)
        if package is None:
            logger.warning("The specified package does not exist, please check your configuration: {}".format(self.path))
            return False
        self.package = package
        self.version = package.version
        return True

    def installed(self):
        if not self.package:
            raise errors.InvalidPackagePath(self.path)
        existing = self.config.resolver.existingPackage(self.package)
        return existing is not None

    def install(self, **arguments):
        # if the supplied package(dealt with in the resolve method), fails
        # to find a valid package from the given path
        # we'll forcibly raise an error
        if self.package is None:
            raise errors.InvalidPackagePath(self.path)
        if self.installed():
            raise errors.PackageAlreadyExists(self.package)
        inplaceInstall = arguments.get("inPlace")
        logger.debug("Running path descriptor: {}.install with arguments: {}".format(self.name, arguments))
        packageDirectory = os.path.join(self.config.packagesPath, self.name, str(self.package.version))
        if not inplaceInstall:
            try:
                installedPkg = self.package.copyTo(self.package, packageDirectory)
                logger.debug("Finished copying: {}->{}".format(self.package, packageDirectory))
            except OSError:
                logger.error("Failed to copy package: {} to destination: {}".format(self.package.name,
                                                                                    packageDirectory),
                             exc_info=True)
                return False
            del self._descriptorDict["path"]
            self._descriptorDict.update({"type": "zootools",
                                         "version": str(self.package.version),
                                         })
        else:
            installedPkg = self.config.resolver.packageFromPath(packageDirectory)
        self.config.resolver.cache[str(installedPkg)] = installedPkg

        self.config.resolver.updateEnvironmentDescriptorFromDict(self._descriptorDict)
        return True
