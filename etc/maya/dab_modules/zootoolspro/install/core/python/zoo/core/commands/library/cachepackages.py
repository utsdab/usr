import logging

from zoo.core import errors
from zoo.core.commands import action
from zoo.core.descriptors import descriptor

logger = logging.getLogger(__name__)


class CachePackages(action.Action):
    """Cache package will ensure all packages defined in the environment has been installed,
    downloaded locally into the packages directory.
    """
    id = "cachePackages"

    def run(self):
        logger.debug("Starting to cache packages")
        loadedEnv = self.config.resolver.loadEnvironmentFile()
        for packageName, rawDescriptor in loadedEnv.items():
            rawDescriptor["name"] = packageName
            descrip = descriptor.descriptorFromDict(self.config,
                                                    rawDescriptor)
            try:
                descrip.resolve()
            except errors.PackageAlreadyExists:
                logger.debug("Package: {} already exists, skipping.".format(descrip.package))
                continue
            descrip.install()
