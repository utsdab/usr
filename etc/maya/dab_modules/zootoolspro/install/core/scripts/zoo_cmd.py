"""CLI python entry point calls the command loader for handling directives.

Internal use only
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

if os.getenv("ZOO_LOG_LEVEL", "INFO") == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def install(rootDirectory, args):
    """Installs zootools into the current environment by calling zooFromPath
    """

    zooCmdDir = os.path.abspath(os.path.dirname(rootDirectory))
    pyFolder = os.path.join(zooCmdDir, "python")
    if pyFolder not in sys.path:
        logger.debug("Installing PythonPath into current environment: {}".format(pyFolder))
        sys.path.append(pyFolder)

    from zoo.core import api
    cfg = api.zooFromPath(zooCmdDir)
    api.setCurrentConfig(cfg)
    if not args:
        cfg.resolver.resolveFromPath(cfg.resolver.environmentPath())
        return
    return api.fromCli(cfg, args)


if __name__ == "__main__":
    root = os.path.dirname(sys.argv[0])
    install(root, sys.argv[1:])
