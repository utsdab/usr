from datetime import datetime

from git import Repo
import git
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class DirtyGitRepoException(Exception):
    pass


class IncorrectCurrentBranchException(Exception):
    pass


class GitCommandError(Exception):
    pass


class InvalidGitRepositoryError(Exception):
    pass


class RepoChecker(object):
    def __init__(self, repoPath=None):
        if repoPath is not None:
            self.repo = Repo(repoPath)
        else:
            self.repo = None
        self.repoPath = repoPath

    @classmethod
    def clone(cls, repoPath, destination, **kwargs):
        rep = Repo.clone_from(repoPath, destination, **kwargs)
        wrapper = cls(os.path.dirname(rep.git_dir))
        return wrapper

    def checkout(self, name):
        self.repo.git.checkout(name)

    def assertRepo(self):
        assert not self.repo.bare
        if self.repo.is_dirty():
            raise DirtyGitRepoException("Current Repo has uncommited changes")

        if not self.repo.active_branch.name == "master":
            raise IncorrectCurrentBranchException(
                "Can't release on branch: {} only master allowed".format(self.repo.active_branch.name))
        return True

    def archive(self, gitVe):
        # ok make a temp directory for downloading the zip
        tempDir = tempfile.mkdtemp()
        archivePath = os.path.join(tempDir, gitVe + ".zip")
        with open(archivePath, "wb") as fp:
            self.repo.archive(fp, format="zip")
        return archivePath

    def tags(self):
        return sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)

    def latestTag(self):

        tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
        if not tags:
            logger.warning("no tags", tags)
            return ""
        return tags[-1].name

    def commit(self, msg):
        logger.info("Commit to current branch, with message: {}".format(msg))
        self.repo.git.add("--all")
        self.repo.git.commit("-m", msg)

    def createTag(self, tag, message):
        logger.info("Creating Tag {} with message: {}".format(tag, message))
        self.newTag = self.repo.create_tag(tag, message=message)

    def pushChanges(self):
        logger.debug("Push local changes")
        self.repo.git.push()

    def pullTags(self):
        self.repo.git.fetch("--tags")

    def pushTag(self):

        logger.info("Pushing next tag {}".format(self.newTag))
        if not self.newTag:
            raise ValueError("No new tag has been created")
        self.repo.remotes.origin.push(self.newTag)
        logger.info("Finished pushing tag {} to remote ".format(self.newTag))

    def commitMessagesSinceTag(self, tagName):
        g = git.Git(self.repoPath)
        commitMsgs = g.log("{}..HEAD".format(tagName), "--oneline", '--pretty=format:[%an] | %ad | %s ')
        for line in iter(commitMsgs.split("\n")):
            if any(i in line for i in ("Merge branch", "Merge remote", "Auto stash")):
                continue
            elif "fatal" in line:
                break
            messageParts = [i.strip() for i in line.split("|")]
            if len(messageParts) < 3:
                continue
            author = messageParts[0]
            date = messageParts[1]
            message = "".join(messageParts[2:])

            info = {"date": datetime.strptime(date, '%a %b %d %H:%M:%S %Y %z'),
                    "author": author,
                    "message": message}
            yield Commit(info)

    def latestCommitMsg(self):
        return self.repo.head.commit.message


class Commit(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(Commit, self).__getattribute__(item)
