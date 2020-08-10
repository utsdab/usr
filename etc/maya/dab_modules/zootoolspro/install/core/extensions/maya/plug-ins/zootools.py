import logging
import os

from maya import OpenMayaMPx
from maya import OpenMaya
from maya import cmds


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
# set the level, we do this for the plugin since this module usually gets executed before zootools is initialized
if os.getenv("ZOO_LOG_LEVEL", "INFO") == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)


def loadZoo():
    rootPath = os.getenv("ZOOTOOLS_PRO_ROOT", "")
    rootPath = os.path.abspath(rootPath)

    if rootPath is None:
        msg = """Zoo Tools PRO is missing the 'ZOOTOOLS_PRO_ROOT' environment variable
        in the maya mod file.
        """
        raise ValueError(msg)
    from zoo.core import api
    currentInstance = api.currentConfig()
    if currentInstance is None:
        coreConfig = api.zooFromPath(rootPath)
        coreConfig.resolver.resolveFromPath(coreConfig.resolver.environmentPath())


def create():
    OpenMaya.MGlobal.displayInfo("Loading Zoo Tools PRO, please wait!")
    logger.debug("Loading Zoo Tools PRO")
    loadZoo()
    try:
        from zoo.libs.utils import env
        if not env.isInMaya:
            logger.debug("Not in maya.exe skipping zootools menu boot")
        else:
            from zoo.apps.toolpalette import run
            run.show()
        logger.debug("Finished Loading Zoo Tools PRO")
        OpenMaya.MGlobal.displayInfo("Zoo Tools PRO")
    except Exception as er:
        logger.error("Failed To load Zoo Tools PRO due to unknown Error",
                     exc_info=True)
        OpenMaya.MGlobal.displayError("Failed to start Zoo Tools PRO\n{}".format(er))


def shutdown():
    from zoo.apps.toolpalette import run
    from zoo.core import api
    OpenMaya.MGlobal.displayInfo("Unloading Zoo Tools PRO, please wait!")
    try:
        logger.debug("Unloading Zoo Tools PRO")
        run.close()
    except Exception:
        logger.error("Failed to shutdown currently loaded tools", exc_info=True)

    currentInstance = api.currentConfig()
    if currentInstance is not None:
        currentInstance.shutdown()
    cmds.flushUndo()


def initializePlugin(obj):
    mplugin = OpenMayaMPx.MFnPlugin(obj, "David Sparrow", "1.0")
    return mplugin.registerUI(create, shutdown)


def uninitializePlugin(obj):
    OpenMayaMPx.MFnPlugin(obj)
