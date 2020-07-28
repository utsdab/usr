# -*- coding: utf-8 -*-

import subprocess
import sys
import logging
import fnmatch
import os
import os.path
import shutil

logging.basicConfig(format="%(module)s - [%(levelname)s] - %(msg)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Include all files from a package, except these
# Think of these as a `.gitignore`
IGNORE = [
    "package.py",
    "rezbuild.py",
    "build",
    ".git",
    "doc*",
    "*.pyc",
    ".cache",
    "__pycache__",
    "*.pyproj",
    "*.sln",
    ".vs",
    ".bez*",
    "build.rxt",
    ".gitignore"
]


def copyBuild(source_path, destination_path):
    for name in os.listdir(source_path):
        if any(fnmatch.fnmatch(name, pat) for pat in IGNORE):
            continue
        src = os.path.join(source_path, name)
        dest = os.path.join(destination_path, name)
        if not os.path.exists(src):
            continue
        if os.path.exists(dest):
            logger.debug("Removing path: {}".format(dest))
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            else:
                os.remove(dest)
        logger.debug("Copying path: {} -> {}".format(src, dest))
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copyfile(src, dest)


def build(source_path, build_path, install_path, targets):
    def _build():
        copyBuild(source_path, build_path)

    def _install():
        copyBuild(source_path, install_path)

    _build()

    if "install" in (targets or []):
        _install()


def main(argv):
    import argparse

    parser = argparse.ArgumentParser("rezbuild")

    parser.add_argument("source_path", type=str)
    parser.add_argument("--build_path",
                        type=str,
                        default=os.getenv("REZ_BUILD_PATH"))
    parser.add_argument("--install_path",
                        type=str,
                        default=os.getenv("REZ_BUILD_INSTALL_PATH"))
    parser.add_argument("--install", type=bool,
                        default=bool(os.getenv("REZ_BUILD_INSTALL")))

    opts = parser.parse_args(argv)

    targets = ["install"] if opts.install else []
    logger.debug(str(opts))
    build(opts.source_path,
          opts.build_path,
          opts.install_path,
          targets)


if __name__ == '__main__':
    main(sys.argv)
