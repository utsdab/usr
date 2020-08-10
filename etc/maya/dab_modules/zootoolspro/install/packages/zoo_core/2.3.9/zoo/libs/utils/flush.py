"""This flush module is a hardcore deletion of modules that live in sys.modules dict
"""
import os
import inspect
from . import zlogging
import sys
import gc

logger = zlogging.zooLogger


def flushUnder(dirpath):
    """Flushes all modules that live under the given directory

    :param dirpath: the name of the top most directory to search under.
    :type dirpath: str
    """
    modulePaths = list()
    for name, module in sys.modules.items():
        if module is None:
            del sys.modules[name]
            continue
        try:
            moduleDirpath = os.path.realpath(os.path.dirname(inspect.getfile(module)))
            if moduleDirpath.startswith(dirpath):
                modulePaths.append((name, inspect.getfile(sys.modules[name])))
                del sys.modules[name]
                logger.debug('unloaded module: %s ' % name)

        except TypeError:
            continue

    # Force a garbage collection
    gc.collect()
    return modulePaths


def reloadZoo():
    """Reload all zoo modules from sys.modules
    This makes it trivial to make changes to plugin that have potentially
    complex reload dependencies.

    .. code-block:: python

        import flush;flush.reloadZoo()

    The above will force all zoo modules to be reloaded by loops over all base packages path in the environment variable
    "ZOO_BASE_PATHS" then calling flushUnder(basePath)
    """

    bases = os.environ.get("ZOO_BASE_PATHS", "").split(os.pathsep)
    for base in bases:
        if os.path.exists(base):
            flushUnder(os.path.realpath(base))


def reloadHard(moduleName):
    """Removes all modules from sys that starts with the module name

    :param moduleName: The module name to remove
    :type moduleName: str
    """
    import sys
    logger = zlogging.zooLogger
    for k in sys.modules.keys():
        if k.startswith(moduleName) or not sys.modules[k]:
            logger.debug("removing module-> %s" % k)
            try:
                del sys.modules[k]
            except TypeError:
                continue
