import logging
import os
import shutil

from zoovendor import pathlib2
from zoo.core.commands import action
from zoo.core.packageresolver import package
from zoo.core.util import filesystem
from zoo.core import constants
from zoo.core import errors

logger = logging.getLogger(__name__)

DEFAULTS = {
    "author": "",
    "authorEmail": "",
    "description": "",
    "displayName": "",
    "environment": {
        "PYTHONPATH": ["{self}"],
        "ZOO_BASE_PATHS": ["{self}"],
        "ZOO_ICON_PATHS": ["{self}/icons"],

    },
    "name": "",
    "requirements": ["zoo_core", "zoo_preferences"],
    "version": "1.0.0",
    "tests": [
        "{self}/tests"
    ]
}


class CreatePackage(action.Action):
    id = "createPackage"

    def arguments(self, argParser):
        argParser.add_argument("--destination",
                               required=True,
                               help="",
                               type=str)
        argParser.add_argument("--name",
                               required=True,
                               help="The name of the package",
                               type=str)
        argParser.add_argument("--displayName",
                               required=False,
                               help="The display name for the package",
                               type=str)
        argParser.add_argument("--author",
                               required=False,
                               default="",
                               type=str)
        argParser.add_argument("--authorEmail",
                               required=False,
                               default="",
                               type=str)
        argParser.add_argument("--description",
                               required=False,
                               help="The tag message",
                               default="",
                               type=str)
        argParser.add_argument("--force",
                               action="store_true",
                               help="If Specified then if the destination exists it will be overridden")

    def run(self):
        existingDescriptor = self.config.descriptorForPackageName(self.options.name)
        if existingDescriptor and self.options.force:
            existingDescriptor.uninstall(remove=True)
        elif existingDescriptor is not None:
            raise errors.PackageAlreadyExists(existingDescriptor.name)
        if os.path.exists(self.options.destination) and self.options.force:
            logger.debug("Removing destination folder: {}".format(self.options.destination))
            shutil.rmtree(self.options.destination)

        elif os.path.exists(self.options.destination):
            raise errors.FileExistsError(self.options.destination)

        destination = pathlib2.Path(self.options.destination, constants.PACKAGE_NAME)

        newPackage = package.Package(destination)
        info = DEFAULTS.copy()
        info["name"] = self.options.name

        newPackage.name = self.options.name
        info["displayName"] = self.options.displayName or self.options.name
        info["author"] = self.options.author
        info["authorEmail"] = self.options.authorEmail
        info["description"] = self.options.description
        newPackage.processData(info)
        subFolder = pathlib2.Path(self.config.corePath) / "python/zoo/core/packageresolver/package_stub"
        if not destination.parent.parent.exists():
            filesystem.ensureFolderExists(destination.parent.parent)
        logger.debug("Copying Stub folder to destination {}".format(self.options.destination))
        shutil.copytree(str(subFolder), self.options.destination, ignore=shutil.ignore_patterns("placeholder*"))
        logger.debug("Finished copying Stub Folder")
        newPackage.save()
        self.config.runCommand("installPackage",
                               ["--path", self.options.destination,
                                "--inPlace"])
