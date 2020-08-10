import logging

from zoo.core.commands import action
from zoo.core.descriptors import descriptor

logger = logging.getLogger(__name__)


class UninstallPackage(action.Action):
    id = "uninstallPackage"

    def arguments(self, argParser):
        argParser.add_argument("--name",
                               required=True,
                               type=str)
        argParser.add_argument("--remove",
                               action="store_true")

    def run(self):
        logger.debug("Running uninstall command for package: {}".format(self.options.name))

        descrip = descriptor.descriptorFromCurrentConfig(self.config,
                                                         self.options.name)
        if not descrip:
            logger.error("No package by the name: {}".format(self.options.name))
            return
        try:
            descrip.resolve()
        except ValueError:
            logger.error("Failed to resolve descriptor: {}".format(self.options.name),
                         exc_info=True, extra=self.options.name)
            return
        descrip.uninstall(self.options.remove)
