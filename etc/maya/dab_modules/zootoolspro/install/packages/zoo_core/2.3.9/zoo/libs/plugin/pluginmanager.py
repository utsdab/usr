"""This module house's the base class of a plugin manager"""

import inspect
import os

from zoo.libs.plugin import plugin
from zoo.libs.utils import modules
from zoo.libs.utils import zlogging
try:
    from inspect import getfullargspec
except ImportError:
    from inspect import getargspec as getfullargspec

logger = zlogging.zooLogger


class PluginManager(object):
    """This class manages a group of plugin instance's.
    use registerPlugin(instance) to registry a instance, automatically discover plugin classes use registerByModule or
    registerByPackage(pkg.path).

    To register a list of paths use instance.registerTools()
    To find out what current plugins are loaded in memory use the instance.loadedPlugins variable
    to return a dictionary.
    To return all plugins currently registry use the instance.plugins variable.
    """

    def __init__(self, interface=plugin.Plugin, variableName=None):
        """

        :param interface: The base class which will become the plugin interface for all plugins for the manager.
        :type interface: class or list
        :param variableName: The class variable name to become the UUID of the class\
        if none is specified the UUID will be the class name.
        :type variableName: str
        """
        self.plugins = {}
        # register the plugin names by the variable, if its missing fallback to the class name
        self.variableName = variableName or ""
        if type(interface) is not list:
            self.interfaces = [interface]
        else:
            self.interfaces = interface
        self.loadedPlugins = {}  # {className: instance}
        self.basePaths = []

    def registerByEnv(self, env):
        """Register's the environment variable value, each path must be separated by os.pathsep

        :param env: The environment variable key
        :type env: str
        """
        paths = os.environ.get(env, "").split(os.pathsep)
        if paths:
            self.registerPaths(paths)

    def registerPaths(self, paths):
        """This function is helper function to register a list of paths.

        :param paths: A list of module or package paths, see registerByModule() and \
        registerByPackage() for the path format.
        :type paths: list(str)
        """
        self.basePaths.extend(paths)
        visited = set()
        for path in paths:
            path = os.path.expandvars(path)
            if not path:
                continue
            elif os.path.isfile(path):
                # remove the extension of the file name so we can deal with py/pyc
                basename = os.extsep.join(path.split(os.extsep)[:-1])
            else:
                basename = path
            if basename in visited:
                continue

            visited.add(basename)
            self.registerPath(path)

    def registerPath(self, modulePath):
        """Registers the given python module path.

        :param modulePath: The absolute full path to a python module
        :type modulePath: str
        :return: Module Object
        """
        importedModule = None
        if os.path.isdir(modulePath):
            self.registerByPackage(modulePath)
            return importedModule
        elif os.path.isfile(modulePath):
            try:
                importedModule = modules.importModule(modules.asDottedPath(os.path.normpath(modulePath)))
            except ImportError:
                logger.error("Failed to import Plugin module: {}, skipped Load".format(modulePath), exc_info=True)
                return importedModule

        elif modules.isDottedPath(modulePath):
            try:
                importedModule = modules.importModule(os.path.normpath(modulePath))
            except ImportError:
                logger.error("Failed to import Plugin module: {}, skipped Load".format(modulePath), exc_info=True)
                return importedModule
        if importedModule:
            self.registerByModule(importedModule)
        return importedModule

    def registerByModule(self, module):
        """ This function registry a module by search all class members of the module and registers any class that is an
        instance of the plugin class 'zoo.libs.plugin.plugin.Plugin'

        :param module: the module path to registry, the path is a '.' separated path eg. zoo.libs.apps.tooldefintions
        :type module: str
        """
        if inspect.ismodule(module):
            for member in modules.iterMembers(module, predicate=inspect.isclass):
                self.registerPlugin(member[1])

    def registerByPackage(self, pkg):
        """This function is similar to registerByModule() but works on packages, this is an expensive operation as it
        requires a recursive search by importing all sub modules and and searching them.

        :param pkg: The package path to register eg. zoo.libs.apps
        :type pkg: str
        """
        for subModule in modules.iterModules(pkg):
            filename = os.path.splitext(os.path.basename(subModule))[0]
            if filename.startswith("__") or subModule.endswith(".pyc"):
                continue
            try:
                subModuleObj = modules.importModule(modules.asDottedPath(os.path.normpath(subModule)))
            except ImportError:
                logger.error("Failed to Import Plugin module: {}".format(subModule),
                             exc_info=True)
                continue
            for member in modules.iterMembers(subModuleObj, predicate=inspect.isclass):
                self.registerPlugin(member[1])

    def registerPlugin(self, classObj):
        """Registers a plugin instance to the manager

        :param classObj: the plugin instance to registry
        :type classObj: Plugin
        """
        for interface in self.interfaces:
            if classObj not in self.plugins.values() and issubclass(classObj, interface):
                name = getattr(classObj, self.variableName) if hasattr(classObj, self.variableName) else classObj.__name__
                logger.debug("registering plugin -> {}".format(name))
                self.plugins[str(name)] = classObj

    def loadPlugin(self, pluginName, **kwargs):
        """Loads a given plugin by name. eg plugin(manager=self)

        :param pluginName: the plugin to load by name
        :type pluginName: str
        """
        tool = self.plugins.get(pluginName)
        if tool:
            logger.debug("Loading Plugin -> {}".format(pluginName))
            # pass the manager into the plugin, this is so we have access to any global info
            spec = getfullargspec(tool.__init__)
            # python 3 and 2 support
            try:
                keywords = spec.kwonlyargs
            except AttributeError:
                keywords = spec.keywords
            args = spec.args

            if (args and "manager" in args) or (keywords and "manager" in keywords):
                kwargs["manager"] = self
            try:
                newTool = tool(**kwargs)
            except Exception:
                logger.error("Failed to load plugin: {}".format(pluginName),
                             exc_info=True)
                return

            self.loadedPlugins[pluginName] = newTool
            self.loadedPlugins[pluginName].isLoaded = True
            return self.loadedPlugins[pluginName]

    def loadAllPlugins(self):
        """Loops over all registered plugins and calls them eg. plugin(manager=self)
        """
        for pluginName in self.plugins:
            self.loadPlugin(pluginName)

    def getPlugin(self, name):
        """Returns the plugin instance by name

        :param name: the name of the plugin
        :type name: str
        :return: Returns the plugin isinstance or None
        :rtype: Plugin instance or None
        """
        if name in self.loadedPlugins:
            return self.loadedPlugins.get(name)
        return self.plugins.get(name)

    def unload(self, name):
        """Unload's a plugin by name from the manager

        :param name: The name of the registered plugin class.
        :type name: str
        :return: Return True if the plugin was successfully unloaded.
        :rtype: bool
        """
        loadedPlugin = self.loadedPlugins.get(name)
        if loadedPlugin and loadedPlugin.isLoaded:
            self.loadedPlugins.pop(name)
            return True
        return False

    def unloadAllPlugins(self):
        """Unloads all currently loaded plugins from the registry.
        """
        self.loadedPlugins = {}
