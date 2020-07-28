import os


def addToEnv(env, newPaths):
    """Adds the specified environment paths to the environment variable
    if the path doesn't already exist.

    :param env: The environment variable name
    :type env: str
    :param newPaths: A iterable containing strings
    :type newPaths: iterable(str)
    """
    # to cull empty strings or strings with spaces
    paths = [i for i in os.getenv(env, "").split(os.pathsep) if i]

    for p in newPaths:
        if p not in paths:
            paths.append(p)
    os.environ[env] = os.pathsep.join(paths)
