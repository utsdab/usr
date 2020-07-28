import glob
import inspect
import os
import sys
import argparse

from zoo.core.commands import action
from zoo.core import constants


class Parser(argparse.ArgumentParser):
    def error(self, message):
        pass


def fromCli(cfg, arguments):
    """A function which runs a zoocli action based on the arguments passed.


    :param cfg:
    :type cfg: :class:`zoo.core.manage.Zoo`
    :param arguments:
    :type arguments: list(str)
    :return:
    :rtype: bool
    """
    argumentParser, subParser = createRootParser()
    for name, clsObj in cfg.commands.items():
        instance = clsObj(config=cfg)
        instance.processArguments(subParser)
    args = argumentParser.parse_args(arguments)
    args.func(args)


def findCommands():
    fileFilter = ("__init__", "__pycache__")
    libPaths = os.getenv(constants.COMMANDLIBRARY_ENV, "")
    visitedShortNames = set()
    commands = {}

    for p in libPaths.split(os.pathsep):
        if not os.path.exists(p):
            continue
        for path in glob.glob(os.path.join(p, "*.py*")):
            basename = os.path.basename(path)
            baseWOExt, ext = os.path.splitext(basename)
            if baseWOExt in fileFilter or baseWOExt in visitedShortNames:
                continue

            name = "zoo.core.commands.{}".format(baseWOExt)
            commandModule = importModule(name, path)
            for mod in inspect.getmembers(commandModule,
                                          predicate=inspect.isclass):
                if issubclass(mod[1], action.Action):
                    commands[mod[1].id] = mod[1]
            visitedShortNames.add(baseWOExt)
    return commands


# py2 and py3 support
if sys.version_info[0] < 3:
    import imp


    def importModule(name, path):
        """Python 2 helper function for importing a python module.

        :param name: The module name
        :type name: str
        :param path: The full path to the module
        :type path: str
        :return: The imported module object
        :rtype: module
        """
        if path.endswith(".py"):
            return imp.load_source(name, path)
        elif path.endswith(".pyc"):
            return imp.load_compiled(name, path)
        return __import__(name)
else:
    import importlib


    def importModule(name, path):
        """Python 3 helper function for importing a python module.

        :param name: The module name
        :type name: str
        :param path: The full path to the module
        :type path: str
        :return: The imported module object
        :rtype: module
        """
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


def createRootParser():
    helpHeader = """
Welcome to the ZooTools Pro

This Command allows you to modify the zootools configuration from a shell.
You can embed zootools python environment by simply running this command without
arguments.
To see the arguments for each zoo command run zoo_cmd [command] --help
    """
    argumentParser = Parser(prog=constants.CLI_ROOT_NAME,
                            description=helpHeader,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
    subParser = argumentParser.add_subparsers()
    return argumentParser, subParser
