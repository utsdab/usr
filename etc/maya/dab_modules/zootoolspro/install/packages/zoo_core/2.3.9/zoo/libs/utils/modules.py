"""This module deals with module paths, importing and the like.
"""
import inspect

import sys
import os
import imp
import importlib

from zoo.libs.utils import zlogging
logger = zlogging.getLogger(__name__)


def importModule(modulePath, name=None):
    """Import's the modulePath, if ModulePath is a dottedPath then the function will use importlib otherwise it's
    expected that modulePath is the absolute path to the source file. If the name arg is not provided then the basename
    without the extension will be used.

    :param modulePath: The module path either a dottedPath eg. zoo.libs.utils.zoomath or a absolute path.
    :type modulePath: str
    :param name: The name for the imported module which will be used if the modulepath is a absolute path.
    :type name: str
    :return: The imported module object
    :rtype: ModuleObject
    """
    if isDottedPath(modulePath) and not os.path.exists(modulePath):
        try:
            return importlib.import_module(modulePath)
        except ImportError:
            logger.error("Failed to load module->{}".format(modulePath), exc_info=True)

    try:
        if os.path.exists(modulePath):
            if not name:
                name = os.path.splitext(os.path.basename(modulePath))[0]
            if name in sys.modules:
                return sys.modules[name]
            if os.path.isdir(modulePath):
                modulePath = os.path.join(modulePath, "__init__.py")
                if not os.path.exists(modulePath):
                    raise ValueError("Cannot find modulepath: {}".format(modulePath))
            return imp.load_source(name, os.path.realpath(modulePath))
    except ImportError:
        logger.error("Failed to load module {}".format(modulePath))
        raise


def iterModules(path, exclude=None):
    """Iterate of the modules of a given folder path

    :param path: str, The folder path to iterate
    :param exclude: list, a list of files to exclude
    :return: iterator
    """
    if not exclude:
        exclude = []
    _exclude = ["__init__.py", "__init__.pyc"]
    for root, dirs, files in os.walk(path):
        if "__init__.py" not in files:
            continue
        for f in files:
            basename = os.path.basename(f)[0]
            if f not in _exclude and basename not in exclude:
                modulePath = os.path.join(root, f)
                if f.endswith(".py") or f.endswith(".pyc"):
                    yield modulePath


def iterMembers(module, predicate=None):
    """Iterates the members of the module, use predicte to restrict to a type

    :param module:Object, the module object to iterate
    :param predicate: inspect.class
    :return:iterator
    """
    for mod in inspect.getmembers(module, predicate=predicate):
        yield mod


def isDottedPath(path):
    """Determines if the path is a dotted path. Bit of a hack

    :param path: str
    :return: bool
    """
    return len(path.split(".")) > 2


def iterSubclassesFromModule(module, classType):
    """Iterates all classes within a module object returning subclasses of type `classType`.

    :param module: the module object to iterate on
    :type module: module object
    :param classType: The class object
    :type classType: object
    :return: genertor function returning class objects
    :rtype: generator(object)
    """
    for member in iterMembers(module, predicate=inspect.isclass):
        if issubclass(member, classType):
            yield member


def asDottedPath(path):
    """ Returns a dotted path relative to the python path.

    .. code-block:: python

        import sys
        currentPath = os.path.expanduser("somerandomPath")
        sys.path.append(currentPath)
        asDottedPath("someRandomPath/subfolder/subsubfolder.py")
        #result: subfolder.subsubfolder

    :param path: the absolute path to convert to a dotted path
    :type path: str
    :return: The dotted path relative to the python
    :rtype: str
    """
    d, f = os.path.split(path)
    f = os.path.splitext(f)[0]
    packagePath = [f]  # __package__ will be a reversed list of package name parts
    syspath = sys.path
    driveLetter = os.path.splitdrive(path)[0] + "\\"
    while d not in syspath:  # go up until we run out of __init__.py files
        d, name = os.path.split(d)  # pull of a lowest level directory name
        if d == driveLetter or name == "":
            return ""
        packagePath.append(name)  # add it to the package parts list
    return ".".join(reversed(packagePath))