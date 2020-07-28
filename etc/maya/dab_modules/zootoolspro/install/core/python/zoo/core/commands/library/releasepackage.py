import logging

from zoo.core.commands import action
from zoo.core import errors

try:
    from zoo.core.util.git import gitwrapper
except ImportError:
    gitwrapper = None

logger = logging.getLogger(__name__)


class ReleasePackage(action.Action):
    """
    Git Release the requested package.
    Requires The package to be of type GIT
    and must exist in current environment File.
    """
    id = "releasePackage"

    def arguments(self, argParser):
        argParser.add_argument("--name",
                               required=True,
                               help="The name of the package to release, this must be the name of "
                                    "an already existing package in the environment",
                               type=str)
        argParser.add_argument("--version",
                               required=True,
                               help="The Version string to apply as a tag",
                               type=str)
        argParser.add_argument("--message",
                               required=False,
                               help="The tag message",
                               type=str)
        argParser.add_argument("--install",
                               help="IF True then the release will be immediately install into current environment",
                               action="store_true")

    def run(self):
        # ensure we've got git installed and git python
        if gitwrapper is None:
            raise errors.MissingGitPython()
        currentDescriptor = self.config.descriptorForPackageName(self.options.name)
        if currentDescriptor is None:
            raise errors.MissingPackage(self.options.name)
        # now lets start the validation process, first convert to a package
        pkg = self.config.resolver.packageForDescriptor(currentDescriptor)
        # assuming we've got git, now validate it
        # first check if its a git repo
        logger.debug("Converting package: {} to gitpython".format(pkg))
        try:
            gitCmd = gitwrapper.RepoChecker(pkg.dirname())
        except gitwrapper.InvalidGitRepositoryError:
            logger.error("Requested package for git release "
                         "isn't of type GIT, type: {}".format(currentDescriptor.type))
            raise ValueError("Package releasing only supports GIT descriptors")
        # check that we have no outstanding changes like commits
        # and branch is master, raising is left to the git wrapper
        logger.debug("Asserting repo of outstanding changes")
        gitCmd.assertRepo()
        # now pull done all tags so we can diff the requested new version
        logger.debug("Pulling tags to ensure the local isn't stale")
        gitCmd.pullTags()
        # now validate the package via git
        currentTags = map(str, list(gitCmd.tags()))

        if self.options.version in currentTags:
            raise errors.GitTagAlreadyExists()
        # update the package with the new version number
        oldVersion = pkg.version
        logger.debug("Updating package version to: {}".format(self.options.version))
        pkg.updateAndWriteVersion(self.options.version)
        try:
            logger.debug("Committed version change")
            # commit the version changes
            gitCmd.commit("Create new version Tag: {}: message: {}".format(self.options.version, self.options.message))
        except gitwrapper.GitCommandError:
            logger.warning("Nothing committed, Possible client updating local version manually, continuing")
        # create a new tag with the version
        gitCmd.createTag(self.options.version,
                         message=self.options.message)
        # push the changes
        gitCmd.pushChanges()
        gitCmd.pushTag()
        # update the current env if requested
        logger.debug("Updating environment requested, version: {} -> {}".format(oldVersion,
                                                                                self.options.version))
        env = self.config.resolver.loadEnvironmentFile()
        env[self.options.name]["version"] = self.options.version

        if self.options.install:
            logger.debug("Running packageInstall command")
            self.config.runCommand("installPackage",
                                   ("--path", pkg.root))
