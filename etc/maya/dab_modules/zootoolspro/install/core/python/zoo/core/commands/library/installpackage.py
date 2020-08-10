import logging

from zoo.core import errors
from zoo.core.commands import action
from zoo.core.descriptors import descriptor

logger = logging.getLogger(__name__)


class InstallPackage(action.Action):
    """Install's the given Package path into the current zoo environment.

    A package can be provided either as a physical storage path or a git
    path and tag.

    """
    id = "installPackage"

    def arguments(self, argParser):
        argParser.add_argument("--path",
                               required=True,
                               type=str,
                               help="Path to either a physical disk location or a https://*/*/*.git path."
                                    "If provide a git path then arguments 'name' and 'tag' should be specified")
        argParser.add_argument("--name",
                               required=False,
                               type=str,
                               help="The name of the package, valid only if 'path' argument is git path")
        argParser.add_argument("--tag",
                               required=False,
                               type=str,
                               help="The git tag to use.")
        argParser.add_argument("--inPlace",
                               action="store_true",
                               help="Valid only if 'path' argument is a physical path. if True then the"
                                    "specified path will be used directly else the package will be copied")

    def run(self):
        path = self.options.path
        tag = self.options.tag
        name = self.options.name
        if not path:
            raise errors.MissingCliArgument("path")

        if path.endswith(".git"):
            if not tag:
                raise errors.MissingCliArgument("tag")
            elif not name:
                raise errors.MissingCliArgument("name")
            descriptorDict = {"path": path,
                              "version": tag,
                              "name": name}
        else:
            descriptorDict = {"path": path}
        logger.debug("Running Install command: {}".format(path))
        descrip = descriptor.descriptorFromPath(self.config,
                                                path,
                                                descriptorDict
                                                )
        try:
            descrip.resolve()
        except ValueError:
            logger.error("Failed to resolve descriptor: {}".format(descriptorDict),
                         exc_info=True, extra=descriptorDict)
            return
        descrip.install(inPlace=self.options.inPlace)
