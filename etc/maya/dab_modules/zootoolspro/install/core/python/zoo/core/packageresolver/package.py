"""
:todo:
    startup/shutdown to support .pyc and py3

"""
import os
import shutil
import sys
import re
import copy
import tempfile
import logging

from distutils import version

from zoo.core import errors, constants
from zoo.core.util import env, filesystem
from zoovendor.six import string_types

logger = logging.getLogger(__name__)


if sys.version[0] == "2":
    import imp


    def importModule(name, path):
        return imp.load_source(name, os.path.realpath(path))
else:
    import importlib.util


    def importModule(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


class Variable(object):
    def __init__(self, key, values):
        self.key = key
        self.values = values
        self.originalValues = values
        envVar = os.getenv(key)
        if envVar:
            self.values.extend([i for i in envVar.split(os.pathsep)])

    def __str__(self):
        if len(self.values) > 1:
            return os.pathsep.join(self.values)
        return self.values[0]

    def split(self, sep):
        return str(self).split(sep)

    def dependencies(self):
        results = set()
        for i in self.values:
            results.union(set(re.findall(constants.DEPENDENT_FILTER, i)))
        return results

    def solve(self, **tokens):
        selfPath = tokens["selftoken"]

        result = [i.replace(constants.PKG_FOLDER_TOKEN, selfPath) for i in self.values]
        self.values = result
        return result


class Package(object):
    # todo: resolve package dependencies

    @classmethod
    def fromData(cls, data):
        pack = cls()
        pack.processData(data)
        return pack

    def __init__(self, packagePath=None):
        self.path = packagePath or ""
        self.root = ""
        # resolved environment
        self.environ = {}
        # cached environment
        self.cache = {}
        self.version = version.LooseVersion()
        self.name = ""
        self.displayName = ""
        self.description = ""
        self.author = ""
        self.authorEmail = ""
        self.tokens = {}
        self.requirements = []
        self.tests = []
        self.resolved = False
        # package startup and shutdown script path
        self.commandPaths = []

        if packagePath is not None and os.path.exists(packagePath):
            self.processFile(packagePath=packagePath)

    def setVersion(self, versionStr):
        self.version = version.LooseVersion(versionStr)
        self.cache["version"] = str(self.version)

    def processFile(self, packagePath):
        self.setPath(packagePath)
        try:
            data = filesystem.loadJson(self.path)
        except ValueError:
            logger.error("Failed to load package due to possible syntax error, {}".format(packagePath))
            data = {}
        self.processData(data)

    def setPath(self, path):
        self.path = os.path.normpath(path)
        self.root = os.path.dirname(path)

    def processData(self, data):

        self.environ = data.get("environment", {})
        self.cache = copy.deepcopy(data)
        self.version = version.LooseVersion(data.get("version", ""))
        self.name = data.get("name", "NO_NAME")
        self.displayName = data.get("displayName", "NO NAME")
        self.description = data.get("description", "NO Description")
        self.tokens = {"selftoken": self.root}
        self.requirements = data.get("requirements", [])
        self.commandPaths = data.get("commands", [])
        self.tests = Variable("tests", data.get("tests", [])).solve(**self.tokens)
        self.author = data.get("author", "")
        self.authorEmail = data.get("authorEmail", "")

    def dirname(self):
        return os.path.dirname(self.path)

    def setName(self, name):
        self.name = name
        self.save()

    def delete(self):
        if os.path.exists(self.root):
            try:
                shutil.rmtree(self.root)
            except OSError:
                logger.error("Failed to remove Package: {}".format(os.path.dirname(self.name)),
                             exc_info=True,
                             extra=self.cache)

    def searchStr(self):
        try:
            return self.name + "-" + str(self.version)
        except AttributeError:
            return self.path + "- (Fail)"

    def __repr__(self):
        return self.searchStr()

    @staticmethod
    def nameForPackageNameAndVersion(packageName, packageVersion):
        return "-".join([packageName, packageVersion])

    def resolve(self, applyEnvironment=True):
        # todo: move to the resolver so dependencies can be resolved
        environ = self.environ
        if not environ:
            logger.warning("Unable to resolve package environment due to invalid package: {}".format(self.path))
            self.resolved = False
            return
        self.commandPaths = Variable("commands", self.commandPaths).solve(**self.tokens)
        pkgVariables = {}
        for k, paths in environ.items():
            # todo: replace using future once we package up future along with zootools
            if isinstance(paths, string_types):
                var = Variable(k, [paths])
            else:
                var = Variable(k, paths)
            var.solve(**self.tokens)
            if applyEnvironment and k != "PYTHONPATH":  # temp, :todo:

                env.addToEnv(k, var.values)
            pkgVariables[k] = var

        if applyEnvironment and "PYTHONPATH" in pkgVariables:
            for i in pkgVariables["PYTHONPATH"].values:
                i = os.path.abspath(i)
                if i not in sys.path:
                    sys.path.append(i)
        logger.debug("Resolved {}: {}".format(self.name, self.root))
        self.resolved = True

    def save(self):
        data = self.cache
        data.update(version=str(self.version),
                    name=self.name,
                    displayName=self.displayName,
                    description=self.description,
                    requirements=self.requirements,
                    author=self.author,
                    authorEmail=self.authorEmail)
        return filesystem.saveJson(data, self.path, indent=4, sort_keys=True)

    def updateAndWriteVersion(self, newVersion):
        data = self.cache
        self.version = newVersion
        data["version"] = str(newVersion)
        if not self.save():
            raise IOError("Failed to save out package json: {}".format(self.path))

    def createZip(self, destinationDirectory=None):
        tempDir = destinationDirectory or tempfile.mkdtemp()
        zipPath = os.path.join(tempDir, "{}-{}.zip".format(self.name, self.version))

        zipped = filesystem.zipdir(self.dirname(), zipPath, constants.FILE_FILTER_EXCLUDE)
        if not zipped:
            logger.error("Failed to write zip to: {}".format(zipPath))
            raise OSError("Failed to write zip file to: {}".format(zipPath))

        return zipPath, tempDir

    @staticmethod
    def copyTo(package, destination):

        if os.path.exists(destination):
            raise errors.FileNotFoundError(destination)
        shutil.copytree(package.dirname(),
                        destination,
                        ignore=shutil.ignore_patterns(*constants.FILE_FILTER_EXCLUDE))
        return Package(os.path.join(destination, constants.PACKAGE_NAME))

    def runStartup(self):
        for commandPath in self.commandPaths:
            if not os.path.exists(commandPath):
                return
            modName = os.path.basename(commandPath).split(os.extsep)[0]
            logger.debug("Importing package startup file: {}".format(commandPath))
            mod = importModule(modName, os.path.realpath(commandPath))
            if hasattr(mod, "startup"):
                logger.debug("Running startup Function for Module: {}".format(commandPath))
                mod.startup(self)
            if modName in sys.modules:
                del sys.modules[modName]

    def shutdown(self):
        for commandPath in self.commandPaths:
            if not os.path.exists(commandPath):
                return
            modName = os.path.basename(os.path.splitdrive(commandPath)[0])

            logger.debug("Importing package startup file: {}".format(commandPath))
            mod = imp.load_source(modName, os.path.realpath(commandPath))
            if hasattr(mod, "shutdown"):
                logger.debug("Running startup Function for Module: {}".format(commandPath))
                mod.shutdown(self)
                del sys.modules[modName]
