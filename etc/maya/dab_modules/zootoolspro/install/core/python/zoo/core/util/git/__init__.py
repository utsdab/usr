from zoo.core.util import processes


def hasGit():
    processes.checkOutput(("git", "--version"))
