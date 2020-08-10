"""
Folder Hierarchy::

    root
        |-hotkeys
        |-tools
            |- toolName
                    |-settingOne.json
                    |SettingTwoFolder
                                |-setting.json

"""
import os
import copy
import shutil
from collections import OrderedDict
from zoo.libs.utils import filesystem
from zoo.libs.utils import zlogging
from zoovendor.pathlib2 import Path

logger = zlogging.getLogger(__name__)


class RootAlreadyExistsError(Exception):
    pass


class RootDoesntExistsError(Exception):
    pass


class InvalidSettingsPath(Exception):
    pass


class InvalidRootError(Exception):
    pass


class ToolSet(object):
    """
    .. code-block:: python

        Create some roots
        tset = ToolSet()
        # the order you add roots is important
        tset.addRoot(os.path.expanduser("~/Documents/maya/2018/scripts/zootools_preferences"), "userPreferences")
        # create a settings instance, if one exists already within one of the roots that setting will be used unless you
        # specify the root to use, in which the associated settingsObject for the root will be returned
        newSetting = tset.createSetting(relative="tools/tests/helloworld",
                                        root="userPreferences",
                                        data={"someData": "hello"})
        print os.path.exists(newSetting.path())
        print newSetting.path()
        # lets open a setting
        foundSetting = tset.findSetting(relative="tools/tests/helloworld", root="userPreferences")

    """

    def __init__(self):
        self.roots = OrderedDict()
        self.extension = ".json"

    def rootNameForPath(self, path):
        for name, root in self.roots.items():
            if str(root).startswith(str(path)):
                return name

    def root(self, name):
        if name not in self.roots:
            raise RootDoesntExistsError("Root by the name: {} doesn't exist".format(name))
        return self._resolveRoot(self.roots[name])

    def _resolveRoot(self, root):
        return Path(os.path.expandvars(os.path.expanduser(str(root)))).resolve()

    def addRoot(self, fullPath, name):
        if name in self.roots:
            raise RootAlreadyExistsError("Root already exists: {}".format(name))
        self.roots[str(name)] = Path(fullPath)

    def deleteRoot(self, root):
        """Deletes the root folder location and all files.

        :param root: the root name to delete
        :type root: str
        :return:
        :rtype: bool
        """
        rootPath = str(self.root(root))
        try:
            shutil.rmtree(rootPath)
        except OSError:
            logger.error("Failed to remove the preference root: {}".format(rootPath),
                         exc_info=True)
            return False
        return True

    def findSetting(self, relativePath, root=None, extension=None):
        """Finds a settings object by searching the roots in reverse order.

        The first path to exist will be the one to be resolved. If a root is specified
        and the root+relativePath exists then that will be returned instead

        :param relativePath:
        :type relativePath: str
        :param root: The Root name to search if root is None then all roots in reverse order will be search until a \
        settings is found.
        :type root: str or None
        :return:
        :rtype: :class:`SettingObject`
        """
        relativePath = Path(relativePath)
        if not relativePath.suffix:
            relativePath = relativePath.with_suffix(extension or self.extension)
        try:
            if root is not None:
                rootPath = self.roots.get(root)
                if rootPath is not None:
                    fullpath = self._resolveRoot(rootPath) / relativePath
                    if not fullpath.exists():
                        return SettingObject(rootPath, relativePath)
                    return self.open(rootPath, relativePath)
            else:
                for name, p in reversed(self.roots.items()):
                    # we're working with an ordered dict
                    resolvedRoot = self._resolveRoot(p)
                    fullpath = resolvedRoot / relativePath
                    if not fullpath.exists():
                        continue
                    return self.open(resolvedRoot, relativePath)
        except ValueError:
            logger.error("failed to load: {} due to syntactical issue", exc_info=True)
            raise

        return SettingObject("", relativePath)

    def settingFromRootPath(self, relativePath, rootPath):
        fullpath = rootPath / relativePath
        if not fullpath.exists():
            return self.open(rootPath, relativePath)
        return SettingObject("", relativePath)

    def createSetting(self, relative, root, data):
        setting = self.findSetting(relative, root)
        setting.update(data)
        return setting

    def open(self, root, relativePath, extension=None):
        relativePath = Path(relativePath)
        if not relativePath.suffix:
            relativePath = relativePath.with_suffix(extension or self.extension)
        fullPath = root / relativePath
        if not fullPath.exists():
            raise InvalidSettingsPath(fullPath)
        data = filesystem.loadJson(str(fullPath))
        return SettingObject(root, relativePath, **data)


class SettingObject(dict):
    """Settings class to encapsulate the json data for a given setting
    """

    def __init__(self, root, relativePath=None, **kwargs):

        relativePath = Path(relativePath or "")
        if not relativePath.suffix:
            relativePath = relativePath.with_suffix(".json")
        kwargs["relativePath"] = relativePath
        kwargs["root"] = root
        super(SettingObject, self).__init__(**kwargs)

    def rootPath(self):
        if self.root:
            return self.root
        return Path()

    def path(self):
        return self.root / self["relativePath"]

    def isValid(self):
        if self.root is None:
            return False
        elif (self.root / self.relativePath).exists():
            return True
        return False

    def __repr__(self):
        return "<{}> root: {}, path: {}".format(self.__class__.__name__, self.root, self.relativePath)

    def __cmp__(self, other):
        return self.name == other and self.version == other.version

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(SettingObject, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self[key] = value

    def save(self, indent=False, sort=False):
        """Saves file to disk as json

        :param indent: If True format the json nicely (indent=2)
        :type indent: bool
        :return fullPath: The full path to the saved .json file
        :rtype fullPath: str
        """
        root = self.root

        if not root:
            return Path()

        fullPath = root / self.relativePath
        filesystem.ensureFolderExists(str(fullPath.parent))
        output = copy.deepcopy(self)
        del output["root"]
        del output["relativePath"]
        exts = fullPath.suffix
        if not exts:
            fullPath = fullPath.with_suffix("json")
        if not indent:
            filesystem.saveJson(output, str(fullPath), sort_keys=sort)
        else:
            filesystem.saveJson(output, str(fullPath), indent=2, sort_keys=sort)

        return self.path()
