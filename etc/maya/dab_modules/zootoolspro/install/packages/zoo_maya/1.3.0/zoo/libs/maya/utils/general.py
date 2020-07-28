import os
from contextlib import contextmanager
import functools

from maya import cmds
from maya.OpenMaya import MGlobal
from maya.api import OpenMaya as om2
from zoo.libs.utils import zlogging
from zoo.libs.maya.utils import env

logger = zlogging.zooLogger


def mayaUpVector():
    """Gets the current world up vector

    :rtype: pw.libs.utils.vectors.Vector
    """
    return MGlobal.upAxis()


def upAxis():
    """Returns the current world up axis in str form.

    :return: returns x,y or z
    :rtype: str
    """
    if isYAxisUp():
        return "y"
    elif isZAxisUp():
        return "z"
    return "x"


def isYAxisUp():
    """Returns True if y is world up

    :return: bool
    """
    return MGlobal.isYAxisUp()


def isZAxisUp():
    """Returns True if Z is world up

    :return: bool
    """
    return MGlobal.isZAxisUp()


def isXAxisUp():
    """Returns True if x is world up

    :return: bool
    """
    return not isYAxisUp() and not isZAxisUp()


def loadPlugin(pluginPath):
    """Loads the given maya plugin path can be .mll or .py

    :param pluginPath: the absolute fullpath file path to the plugin
    :type pluginPath: str
    :rtype: bool
    """
    try:
        if not isPluginLoaded(pluginPath):
            cmds.loadPlugin(pluginPath)
    except RuntimeError:
        logger.debug("Could not load plugin->{}".format(pluginPath))
        return False
    return True


def unloadPlugin(pluginPath):
    """unLoads the given maya plugin name can be .mll or .py

    :param pluginPath: Maya plugin name
    :type pluginPath: str
    :rtype: bool
    """
    try:
        if isPluginLoaded(pluginPath):
            cmds.unloadPlugin(pluginPath)
    except RuntimeError:
        logger.debug("Could not load plugin->{}".format(pluginPath))
        return False
    return False


def isPluginLoaded(pluginPath):
    """Returns True if the given plugin name is loaded
    """
    return cmds.pluginInfo(pluginPath, q=True, loaded=True)


def getMayaPlugins():
    location = env.getMayaLocation(env.mayaVersion())
    plugins = set()
    for path in [i for i in env.mayaPluginPaths() if i.startswith(location) and os.path.isdir(i)]:
        for x in os.listdir(path):
            if os.path.isfile(os.path.join(path, x)) and isPluginLoaded(path):
                plugins.add(x)
    return list(plugins)


def loadAllMayaPlugins():
    logger.debug("loading All plugins")
    for plugin in getMayaPlugins():
        loadPlugin(plugin)
    logger.debug("loaded all plugins")


def unLoadMayaPlugins():
    logger.debug("unloading All plugins")
    for plugin in getMayaPlugins():
        unloadPlugin(plugin)
    logger.debug("unloaded all plugins")


def removeUnknownPlugins():
    removedPlugins = set()
    for pluginName in cmds.unknownPlugin(query=True, list=True) or []:
        cmds.unknownPlugin(pluginName, remove=True)
        removedPlugins.add(removedPlugins)


@contextmanager
def namespaceContext(namespace):
    currentNamespace = om2.MNamespace.currentNamespace()
    existingNamespaces = om2.MNamespace.getNamespaces(currentNamespace, True)
    if currentNamespace != namespace and namespace not in existingNamespaces and namespace != om2.MNamespace.rootNamespace():
        try:
            om2.MNamespace.addNamespace(namespace)
        except RuntimeError:
            logger.error("Failed to create namespace: {}, existing namespaces: {}".format(namespace,
                                                                                          existingNamespaces),
                         exc_info=True)
            om2.MNamespace.setCurrentNamespace(currentNamespace)
            raise
    om2.MNamespace.setCurrentNamespace(namespace)
    try:
        yield
    finally:
        om2.MNamespace.setCurrentNamespace(currentNamespace)


@contextmanager
def isolatedNodes(nodes, panel):
    """Context manager for isolating `nodes` in maya model `panel`

    :param nodes: A list of node fullpaths to isolate
    :type nodes: seq(str)
    :param panel: The maya model panel
    :type panel: str
    """

    cmds.isolateSelect(panel, state=True)
    for obj in nodes:
        cmds.isolateSelect(panel, addDagObject=obj)
    yield
    cmds.isolateSelect(panel, state=False)


def undoDecorator(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True)
            return func(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)

    return inner
