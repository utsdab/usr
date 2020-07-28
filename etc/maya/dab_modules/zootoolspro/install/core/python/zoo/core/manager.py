import os
import logging

from zoo.core import errors
from zoo.core.commands import loader
from zoo.core.packageresolver import resolver
from zoo.core.descriptors import descriptor
from zoo.core import constants
from zoo.core.util import env, filesystem
from zoovendor import pathlib2

logger = logging.getLogger(__name__)


class Zoo(object):
    """Zoo class is the the main entry point into operating on
    any part of zoo tools.

    use zoo.resolver to access the current package environment.
    """

    def __init__(self, zooPath):
        """ Initializes the default paths for zootools

        Raises :class:`errors.FileNotFoundError` in the case where the provided
        pat doesn't exist.

        :param zooPath: The root location of zootools root folder i.e the one above \
        the install folder.
        :type zooPath: str
        :raise :class:`errors.FileNotFoundError`
        """
        if not os.path.exists(zooPath):
            raise errors.FileNotFoundError(zooPath)
        zooPaths = _resolveZooPathsFromPath(zooPath)
        logger.debug("Initializing zootools from zooPath: {}: {}".format(zooPath, zooPaths),
                     extra=zooPaths)
        if not os.getenv(constants.ZOO_ADMIN):
            self.isAdmin = False
        self._rootPath = zooPaths["root"]  # type: str
        self._corePath = zooPaths["core"]  # type: str
        self._pyFolderPath = zooPaths["python"]  # type: str
        self._configPath = zooPaths["config"]  # type: str
        self._packagesPath = zooPaths["packages"]  # type: str
        self._resolver = resolver.Environment(self)
        self._commandLibCache = loader.findCommands()

    def coreVersion(self):
        """Returns core(this) package version string.

        :return: coreVersion ie. "1.0.0"
        :rtype: str
        """
        package = os.path.join(self._corePath, "zoo_package.json")
        packageInfo = filesystem.loadJson(package)
        return packageInfo["version"]

    def buildVersion(self):
        """Returns the Zoo Tools build version string.

        :return: buildVersion ie. "1.0.0"
        :rtype: str
        """
        package = self.buildPackagePath()
        if not package.exists():
            return "DEV"
        buildPackage = filesystem.loadJson(str(package))
        return buildPackage.get("version", "DEV")

    def buildPackagePath(self):
        """Returns the fullPath to the zoo_package.json which is the build package.

        :return: :class:`pathlib2.Path`
        """
        return pathlib2.Path(self._rootPath) / "zoo_package.json"

    @property
    def isAdmin(self):
        """Returns whether or not the current user is in admin mode.

        :return: True if admin
        :rtype: bool
        """
        return bool(int(os.getenv(constants.ZOO_ADMIN, "0")))

    @isAdmin.setter
    def isAdmin(self, state):
        os.environ[constants.ZOO_ADMIN] = str(int(state))

    @property
    def commands(self):
        """Returns the executable cli commands dict cache.

        :return: commandId: classObject
        :rtype: dict
        """
        return self._commandLibCache

    @property
    def rootPath(self):
        """Returns the root path of zootools.

        The root path directory is the folder above the install folder

        :return: The root folder of zootools
        :rtype: str
        """
        return self._rootPath

    @property
    def configPath(self):
        """Returns the config folder which sits below the root.

        :return: The config folder for zootools
        :rtype: str
        """
        return self._configPath

    @property
    def corePath(self):
        """The core folder of zootools which is relative to the root under the
        install folder.

         The core folder houses internal logic of zootools package management.

        :return: The core folder
        :rtype: str
        """
        return self._corePath

    @property
    def packagesPath(self):
        """Returns the package repository path under the zootools/install folder.

        This folder is the location for all installed packages.
        Each package Housed here is in the form of::

            Packages
                - packageName
                    - packageVersion(LooseVersion)
                        -code

        :return: The packages folder
        :rtype: str
        """
        return self._packagesPath

    @property
    def resolver(self):
        """Returns the environment resolver instance which contains the
        package cache.

        :return: The Environment Resolver instance
        :rtype: :class:`zoo.core.packageresolver.Environment`
        """
        return self._resolver

    def descriptorFromDict(self, descriptorDict):
        """Helper method which calls for :func:`descriptor.descriptorFromDict`

        :param descriptorDict: See :func:`descriptor.descriptorFromDict` for more info
        :type descriptorDict: dict
        :return: The corresponding Descriptor instance
        :rtype: :class:`Descriptor`
        """
        return descriptor.descriptorFromDict(self, descriptorDict)

    def descriptorForPackageName(self, name):
        """Returns the matching descriptor instance for the package name.

        :param name: The zoo package name to find.
        :type name: str
        :return: The descriptor or None
        :rtype: :class:`descriptor.Descriptor` or None
        """
        return descriptor.descriptorFromCurrentConfig(self, name)

    def runCommand(self, commandName, arguments):
        """Run's the specified CLI command.

        User runCommand("commandName", ["--help"] to get the comamnd help

        :param commandName: The command Id name
        :type commandName: str
        :param arguments: List of cls commands to pass to the command
        :type arguments: list(str)
        :return: True if the command was run
        :rtype: bool
        """
        commandObj = self._commandLibCache.get(commandName)
        if not commandObj:
            return
        argumentsCopy = list(arguments)
        if commandName not in arguments:
            argumentsCopy.insert(0, commandName)
        argumentParser, subParser = loader.createRootParser()
        instance = commandObj(config=self)
        instance.processArguments(subParser)

        args = argumentParser.parse_args(argumentsCopy)

        args.func(args)

    def shutdown(self):
        """Shutdown Method for zootools excluding Host application plugin related code.
        """
        self.resolver.shutdown()
        # clear out the sys.modules of all zoo modules currently in memory
        from zoo.core.util import flush
        flush.reloadZoo()
        setCurrentConfig(None)

    def reload(self):
        root = self.rootPath
        self.shutdown()
        cfg = zooFromPath(root)
        cfg.resolver.resolveFromPath(cfg.resolver.environmentPath())
        return cfg



# global storage of zoo config,
# note: i'm not all that happy with globals but we need a way
# to handle caching of the environment to avoid re-calculating
# packages. I would also like to avoid singletons here.
_ZOO_CONFIG_CACHE = None


def currentConfig():
    """Returns the :class:`Zoo` instance currently initialized globally.

    If this func returns None call :func: `zooFromPath`.

    :return: The currently initialized :class:`Zoo`
    :rtype: :class:`Zoo` or None
    """
    global _ZOO_CONFIG_CACHE
    return _ZOO_CONFIG_CACHE


def setCurrentConfig(config):
    """Sets the :class:`Zoo` global instance.

    :warning: This overrides the global instanced :class:`Zoo` instance.

    If you need to run multiple instances in parallel use :func:`zooConfig`
    """

    global _ZOO_CONFIG_CACHE
    _ZOO_CONFIG_CACHE = config


def zooFromPath(path):
    """Returns the zootools instance for the given root path.

    :param path: The root path of zootools to initialize, \
    See :class:`Zoo` for more information.
    :type path: str
    :return: The zoo instance.
    :rtype: :class:`Zoo`
    """
    assert os.path.exists(path), "Path doesn't exist: {}".format(path)
    cfg = Zoo(path)
    setCurrentConfig(cfg)

    return cfg


def _resolveZooPathsFromPath(path):
    """ Internal function which resolves the zootools main paths

    Resolves "root","config","core","packages"
    :todo  config, package folders to be part of the environment and applied here.
    """
    logger.debug("Resolving zootools from supplied path: {}".format(path))
    installFolder = os.path.join(path, "install")
    cfgFolder = os.path.join(path, constants.CONFIG_FOLDER_NAME)
    pkgFolder = os.path.join(path, "install", constants.PKG_FOLDER_NAME)
    outputPaths = dict(config=cfgFolder,
                       packages=pkgFolder,
                       root=path
                       )
    if os.path.exists(installFolder):
        logger.debug("Folder Install Folder: {}".format(installFolder))
        outputPaths["python"] = os.path.join(installFolder, "core", "python")
        outputPaths["core"] = os.path.join(installFolder, "core")
    else:
        # ok one last check by walk two folders up an check to see
        # if the install folder exists, if not we assume we're running vanilla.
        # path is the core folder python folder here
        walkedRoot = os.path.abspath(os.path.join(path, "..", ".."))
        walkedInstallFolder = os.path.abspath(os.path.join(walkedRoot, "install"))
        if os.path.exists(walkedInstallFolder):
            logger.debug("Found root folder: {}".format(walkedRoot))
            outputPaths["root"] = walkedRoot
            outputPaths["core"] = os.path.join(walkedInstallFolder, "core")
            outputPaths["python"] = os.path.join(walkedInstallFolder, "core", "python")
            outputPaths["config"] = os.path.join(walkedRoot, constants.CONFIG_FOLDER_NAME)
            outputPaths["packages"] = os.path.join(walkedInstallFolder, constants.PKG_FOLDER_NAME)
        else:
            logger.debug("Couldn't find install folder, falling back to base install solution: {}".format(path))
            # in this case the install folder doesn't exist at all and
            # we're running in uninstall vanilla state, in which
            # case initialize zootools without the folders at all
            outputPaths["config"] = ""
            outputPaths["core"] = path
            outputPaths["python"] = os.path.join(path, "python")
            outputPaths["packages"] = ""
    env.addToEnv(constants.COMMANDLIBRARY_ENV,
                 [os.path.join(outputPaths["python"], "zoo", "core", "commands", "library")])
    return outputPaths
